from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
import json
import hashlib
import secrets
import time
import os
from typing import List, Optional
import bcrypt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from pathlib import Path
import pytz
import random

# Explicitly find and load the .env file from the project root
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


app = FastAPI(title="CryptoSim API", version="1.0.0")

# CORS middleware for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
redis_host = os.getenv("UPSTASH_REDIS_REST_URL", "localhost")
redis_port = int(os.getenv("UPSTASH_REDIS_REST_PORT", 6379))
redis_password = os.getenv("UPSTASH_REDIS_REST_PASSWORD", "")

redis_config = {
    "host": redis_host,
    "port": redis_port,
    "password": redis_password,
    "decode_responses": True,
}

if "upstash.io" in redis_host:
    redis_config["ssl"] = True

redis_client = redis.Redis(**redis_config)

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str
    wallet_address: str
    balance: float
    total_mined: float

class LeaderboardEntry(BaseModel):
    username: str
    balance: float
    total_mined: float
    rank: int

class MiningResult(BaseModel):
    success: bool
    coins_earned: float
    hash_found: str
    difficulty: int

class TransferPayload(BaseModel):
    recipient_wallet_address: str
    amount: float

class SyncPayload(BaseModel):
    proofs: List[dict]

class StatsResponse(BaseModel):
    total_coins_in_circulation: float
    total_users: int

class GroupJob(BaseModel):
    job_id: str
    total_hashes: int
    hashes_completed: int
    reward_per_hash: float
    difficulty: int
    status: str
    expires_at: str
    challenges: List[str]

class SubmitProofPayload(BaseModel):
    job_id: str
    challenge: str
    nonce: int
    hash_found: str

class ActivityLog(BaseModel):
    timestamp: str
    action: str
    amount: float
    note: str

# Helper functions
def get_est_time():
    """Returns the current time in Eastern Standard Time as an ISO 8601 string."""
    utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
    est_tz = pytz.timezone('US/Eastern')
    return utc_now.astimezone(est_tz).isoformat()

def add_activity(username: str, action: str, amount: float, note: str):
    """Adds a new entry to a user's activity log."""
    log_key = f"activity:{username}"
    log_entry = {
        "timestamp": get_est_time(),
        "action": action,
        "amount": amount,
        "note": note
    }
    # LPUSH adds the new entry to the start of the list
    redis_client.lpush(log_key, json.dumps(log_entry))
    # LTRIM keeps the list capped at the most recent 10 entries
    redis_client.ltrim(log_key, 0, 9)

def manage_group_jobs():
    """
    Checks active group jobs. If any are completed or expired, replaces them.
    Ensures there are always 3 active jobs.
    """
    active_jobs_key = "group_jobs:active"
    
    # Prune completed or expired jobs
    active_job_ids = redis_client.smembers(active_jobs_key)
    for job_id in active_job_ids:
        job_key = f"job:{job_id}"
        if not redis_client.exists(job_key) or redis_client.hget(job_key, "status") == "completed":
            redis_client.srem(active_jobs_key, job_id)
            continue
        
        expires_at_str = redis_client.hget(job_key, "expires_at")
        if expires_at_str and datetime.fromisoformat(expires_at_str) < datetime.now(timezone.utc):
            redis_client.hset(job_key, "status", "expired")
            redis_client.srem(active_jobs_key, job_id)

    # Replenish jobs if needed
    while redis_client.scard(active_jobs_key) < 3:
        job_id = secrets.token_hex(8)
        job_key = f"job:{job_id}"
        
        # Check if this job_id somehow already exists to prevent overwriting
        if redis_client.exists(job_key):
            continue

        job_size = random.choice([16, 24, 32, 40, 48, 56, 64])
        difficulty = random.choice([5, 6, 7])
        
        # New reward structure with difficulty multipliers
        base_reward_per_hash = 0.001
        base_bonus = 0.01

        difficulty_multipliers = {
            5: 1.0,   # Easy
            6: 1.15,  # Intermediate
            7: 1.3    # Hard
        }
        
        # Scale base rewards by job size
        size_multiplier = job_size / 16
        reward_per_hash = base_reward_per_hash * size_multiplier
        
        job_data = {
            "total_hashes": job_size,
            "hashes_completed": 0,
            "reward_per_hash": reward_per_hash,
            "difficulty": difficulty,
            "status": "active",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        }
        
        # Create the set of hashes to be solved for this job FIRST
        hashes_to_solve_key = f"job:{job_id}:hashes"
        challenges = [secrets.token_hex(16) for _ in range(job_size)]
        
        # Use a pipeline to ensure atomicity
        pipe = redis_client.pipeline()
        pipe.hset(job_key, mapping=job_data)
        pipe.sadd(hashes_to_solve_key, *challenges)
        pipe.sadd(active_jobs_key, job_id)
        pipe.execute()

def generate_wallet_address():
    """Generate a unique wallet address"""
    return f"0x{secrets.token_hex(20)}"

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def get_user_by_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get user from JWT token"""
    try:
        token = credentials.credentials
        # Simple token validation (in production, use proper JWT)
        user_data = redis_client.get(f"token:{token}")
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid token")
        return json.loads(user_data)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/sync", status_code=status.HTTP_200_OK)
async def sync_offline_activity(payload: SyncPayload, current_user: dict = Depends(get_user_by_token)):
    """
    Validates and syncs proofs of work done offline.
    """
    user_data_str = redis_client.get(f"user:{current_user['username']}")
    if not user_data_str:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user_data = json.loads(user_data_str)
    
    total_coins_earned = 0.0
    valid_proofs_count = 0

    for proof in payload.proofs:
        # Basic validation of proof structure
        if not all(k in proof for k in ['challenge', 'nonce', 'hash_found', 'difficulty']):
            continue # or raise a specific error

        challenge = proof['challenge']
        nonce = proof['nonce']
        hash_found = proof['hash_found']
        difficulty = proof['difficulty']

        # Re-calculate the hash to verify the proof
        test_string = f"{challenge}{nonce}"
        verify_hash = hashlib.sha256(test_string.encode()).hexdigest()

        if verify_hash == hash_found and verify_hash.startswith('0' * difficulty):
            # Proof is valid, calculate reward (must match online rewards)
            base_reward = 0.0005 # Reduced from 0.001
            difficulty_bonus = difficulty * 0.0005
            coins_earned = base_reward + difficulty_bonus
            total_coins_earned += coins_earned
            valid_proofs_count += 1

    if valid_proofs_count > 0:
        user_data["balance"] += total_coins_earned
        user_data["total_mined"] += total_coins_earned
        
        # Save updated user data
        redis_client.set(f"user:{current_user['username']}", json.dumps(user_data))
        
        # Update leaderboard
        redis_client.zadd("leaderboard", {current_user['username']: user_data["balance"]})

        # Add activity log entry
        add_activity(current_user['username'], "sync_offline", total_coins_earned, f"Hash: {hash_found[:12]}...")

    return {
        "message": f"Sync successful. Validated {valid_proofs_count} of {len(payload.proofs)} proofs.",
        "total_coins_synced": total_coins_earned,
        "new_balance": user_data["balance"]
    }

# API Routes
@app.get("/")
async def root():
    return {"message": "CryptoSim API is running!", "status": "online"}

@app.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    """Register a new user"""
    # Check if username already exists
    if redis_client.exists(f"user:{user.username}"):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create user
    wallet_address = generate_wallet_address()
    hashed_password = hash_password(user.password)
    
    user_data = {
        "username": user.username,
        "password_hash": hashed_password,
        "wallet_address": wallet_address,
        "balance": 0.0,
        "total_mined": 0.0,
        "created_at": datetime.now().isoformat()
    }
    
    # Store user data
    redis_client.set(f"user:{user.username}", json.dumps(user_data))
    redis_client.set(f"wallet:{wallet_address}", user.username)
    
    # Add to leaderboard
    redis_client.zadd("leaderboard", {user.username: 0.0})
    
    return UserResponse(
        username=user.username,
        wallet_address=wallet_address,
        balance=0.0,
        total_mined=0.0
    )

@app.post("/login")
async def login_user(user: UserLogin):
    """Login user and return token"""
    # Get user data
    user_data = redis_client.get(f"user:{user.username}")
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_data = json.loads(user_data)
    
    # Verify password
    if not verify_password(user.password, user_data["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Invalidate any old tokens for this user to enforce one session at a time
    old_token = redis_client.get(f"user_token:{user.username}")
    if old_token:
        redis_client.delete(f"token:{old_token}")

    # Generate token
    token = secrets.token_urlsafe(32)
    redis_client.setex(f"token:{token}", 3600, json.dumps({
        "username": user.username,
        "wallet_address": user_data["wallet_address"]
    }))
    # Store a reverse mapping to find and invalidate old tokens
    redis_client.setex(f"user_token:{user.username}", 3600, token)
    
    return {"token": token, "username": user.username}

@app.post("/logout", status_code=status.HTTP_200_OK)
async def logout_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Invalidates the user's current token, effectively logging them out."""
    token = credentials.credentials
    user_data_str = redis_client.get(f"token:{token}")
    
    # Find the associated user and remove the reverse mapping
    if user_data_str:
        user_data = json.loads(user_data_str)
        username = user_data.get("username")
        if username:
            redis_client.delete(f"user_token:{username}")
    
    # Delete the primary token
    redis_client.delete(f"token:{token}")
    
    return {"message": "Logged out successfully"}

@app.post("/transfer", status_code=status.HTTP_200_OK)
async def transfer_coins(payload: TransferPayload, current_user: dict = Depends(get_user_by_token)):
    """
    Transfers coins from the current user to a recipient's wallet.
    """
    sender_username = current_user['username']
    recipient_wallet_address = payload.recipient_wallet_address
    amount = payload.amount

    # --- Validation ---
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transfer amount must be positive.")

    # Find recipient's username from their wallet address
    recipient_username = redis_client.get(f"wallet:{recipient_wallet_address}")
    if not recipient_username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient wallet address not found.")

    if sender_username == recipient_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot send coins to yourself.")

    # --- Get User Data ---
    sender_data_str = redis_client.get(f"user:{sender_username}")
    recipient_data_str = redis_client.get(f"user:{recipient_username}")

    if not sender_data_str or not recipient_data_str:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User data not found.")

    sender_data = json.loads(sender_data_str)
    recipient_data = json.loads(recipient_data_str)

    # Check for sufficient balance
    if sender_data["balance"] < amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds.")

    # --- Perform Transaction ---
    sender_data["balance"] -= amount
    recipient_data["balance"] += amount

    # --- Update Database ---
    # Use a pipeline for atomicity
    pipe = redis_client.pipeline()
    pipe.set(f"user:{sender_username}", json.dumps(sender_data))
    pipe.set(f"user:{recipient_username}", json.dumps(recipient_data))
    pipe.zadd("leaderboard", {sender_username: sender_data["balance"]})
    pipe.zadd("leaderboard", {recipient_username: recipient_data["balance"]})
    pipe.execute()

    # --- Add Activity Logs ---
    add_activity(sender_username, "send", -amount, f"To: {recipient_username[:8]}...")
    add_activity(recipient_username, "receive", amount, f"From: {sender_username}")

    return {
        "message": "Transfer successful",
        "sender_new_balance": sender_data["balance"],
        "recipient_username": recipient_username
    }

@app.get("/stats", response_model=StatsResponse)
async def get_app_stats():
    """
    Calculates and returns application-wide statistics.
    """
    # Get all scores (balances) from the leaderboard
    all_users_with_scores = redis_client.zrange("leaderboard", 0, -1, withscores=True)
    
    total_coins = sum(score for member, score in all_users_with_scores)
    total_users = len(all_users_with_scores)

    return {
        "total_coins_in_circulation": total_coins,
        "total_users": total_users
    }

@app.post("/admin/clear-all-jobs", status_code=200)
async def admin_clear_jobs():
    """
    TEMPORARY ADMIN FUNCTION: Deletes all active group jobs, forcing regeneration.
    """
    active_jobs_key = "group_jobs:active"
    active_job_ids = redis_client.smembers(active_jobs_key)
    
    pipe = redis_client.pipeline()
    for job_id in active_job_ids:
        pipe.delete(f"job:{job_id}")
        pipe.delete(f"job:{job_id}:hashes")
        pipe.delete(f"job:{job_id}:contributors")
    
    pipe.delete(active_jobs_key)
    pipe.execute()

    return {"message": f"Successfully deleted {len(active_job_ids)} active jobs. New jobs will be generated on the next request to /groupjobs."}

@app.get("/groupjobs", response_model=List[GroupJob])
async def get_group_jobs(current_user: dict = Depends(get_user_by_token)):
    """
    Manages and retrieves the list of active group jobs.
    """
    manage_group_jobs() # Ensure jobs are up-to-date before serving
    
    active_job_ids = redis_client.smembers("group_jobs:active")
    jobs = []
    for job_id in active_job_ids:
        job_data = redis_client.hgetall(f"job:{job_id}")
        if job_data:
            # Also fetch the list of unsolved challenges
            challenges = redis_client.smembers(f"job:{job_id}:hashes")
            job_data['challenges'] = list(challenges)
            jobs.append(GroupJob(job_id=job_id, **job_data))
    return sorted(jobs, key=lambda j: j.total_hashes)

@app.post("/groupjobs/submit", status_code=status.HTTP_200_OK)
async def submit_group_job_proof(payload: SubmitProofPayload, current_user: dict = Depends(get_user_by_token)):
    """
    Submits a proof of work for a single hash in a group job.
    """
    job_id = payload.job_id
    challenge = payload.challenge # This is one of the hashes from the job's set
    nonce = payload.nonce
    hash_found = payload.hash_found

    job_key = f"job:{job_id}"
    hashes_to_solve_key = f"job:{job_id}:hashes"

    # --- Validation ---
    if not redis_client.exists(job_key) or redis_client.hget(job_key, "status") != "active":
        raise HTTPException(status_code=400, detail="This job is no longer active.")

    # Verify the proof of work itself
    difficulty = int(redis_client.hget(job_key, "difficulty"))
    test_string = f"{challenge}{nonce}"
    verify_hash = hashlib.sha256(test_string.encode()).hexdigest()

    if not (verify_hash == hash_found and verify_hash.startswith('0' * difficulty)):
        raise HTTPException(status_code=400, detail="Invalid proof of work.")

    # --- Atomically check and claim the hash ---
    # SREM returns 1 if the element was removed, 0 if it wasn't there (i.e., someone else got it first)
    if redis_client.srem(hashes_to_solve_key, challenge) == 0:
        raise HTTPException(status_code=409, detail="Hash already solved by another user. Try again!")

    # --- Award and Update ---
    user_data_str = redis_client.get(f"user:{current_user['username']}")
    user_data = json.loads(user_data_str)
    
    reward_per_hash = float(redis_client.hget(job_key, "reward_per_hash"))
    
    user_data["balance"] += reward_per_hash
    user_data["total_mined"] += reward_per_hash
    
    # --- Track Contribution ---
    contribution_key = f"job:{job_id}:contributors"
    # HINCRBY will increment the user's contribution count for this job by 1
    redis_client.hincrby(contribution_key, current_user['username'], 1)

    hashes_completed = redis_client.hincrby(job_key, "hashes_completed", 1)
    
    # --- Finalize ---
    pipe = redis_client.pipeline()
    pipe.set(f"user:{current_user['username']}", json.dumps(user_data))
    pipe.zadd("leaderboard", {current_user['username']: user_data["balance"]})
    
    # Check if this was the final hash
    total_hashes = int(redis_client.hget(job_key, "total_hashes"))
    job_was_completed = False
    if hashes_completed >= total_hashes:
        job_was_completed = True
        pipe.hset(job_key, "status", "completed")
        pipe.srem("group_jobs:active", job_id)

    pipe.execute()

    # Add activity log for the individual hash
    add_activity(current_user['username'], "group_mine", reward_per_hash, f"Job: {job_id[:8]}...")

    # --- Distribute Bonus if Job was Completed ---
    if job_was_completed:
        bonus_pools = {16: 0.01, 32: 0.0205, 64: 0.0425}
        bonus_amount = bonus_pools.get(total_hashes, 0)
        user_specific_bonuses = {} # Initialize dictionary here

        contributors = redis_client.hgetall(contribution_key)
        total_contributions = sum(int(c) for c in contributors.values())

        if bonus_amount > 0 and total_contributions > 0:
            bonus_pipe = redis_client.pipeline()
            
            for username, count_str in contributors.items():
                contribution_count = int(count_str)
                percentage = contribution_count / total_contributions
                user_bonus = bonus_amount * percentage
                user_specific_bonuses[username] = user_bonus
                
                # Fetch user, update balance, and save
                contrib_user_data_str = redis_client.get(f"user:{username}")
                if contrib_user_data_str:
                    contrib_user_data = json.loads(contrib_user_data_str)
                    contrib_user_data["balance"] += user_bonus
                    
                    bonus_pipe.set(f"user:{username}", json.dumps(contrib_user_data))
                    bonus_pipe.zadd("leaderboard", {username: contrib_user_data["balance"]})
                    
                    # Use a separate function call for activity log to ensure correct timestamp
                    add_activity(username, "group_bonus", user_bonus, f"Job: {job_id[:8]} Completed!")
            
            bonus_pipe.execute()

    final_response = {
        "message": "Proof accepted! Reward granted.",
        "new_balance": user_data["balance"],
        "job_id": job_id,
        "hashes_completed": hashes_completed,
        "total_hashes": total_hashes
    }

    if job_was_completed:
        my_bonus = user_specific_bonuses.get(current_user['username'], 0)
        final_response["bonus_awarded"] = my_bonus
        final_response["message"] = "Final proof accepted! Job complete. Bonus distributed."

    return final_response

@app.get("/activity", response_model=List[ActivityLog])
async def get_activity(current_user: dict = Depends(get_user_by_token)):
    """
    Retrieves the last 10 activity log entries for the current user.
    """
    log_key = f"activity:{current_user['username']}"
    raw_logs = redis_client.lrange(log_key, 0, 9)
    
    activity_logs = [json.loads(log) for log in raw_logs]
    return activity_logs

@app.get("/balance", response_model=UserResponse)
async def get_balance(current_user: dict = Depends(get_user_by_token)):
    """Get user's current balance"""
    user_data = redis_client.get(f"user:{current_user['username']}")
    user_data = json.loads(user_data)
    
    return UserResponse(
        username=user_data["username"],
        wallet_address=user_data["wallet_address"],
        balance=user_data["balance"],
        total_mined=user_data["total_mined"]
    )

@app.post("/mine", response_model=MiningResult)
async def mine_crypto(current_user: dict = Depends(get_user_by_token)):
    """Mine cryptocurrency by solving hash puzzles"""
    # Get user data
    user_data = redis_client.get(f"user:{current_user['username']}")
    user_data = json.loads(user_data)
    
    # Generate mining challenge
    challenge = secrets.token_hex(16)
    target_difficulty = 5  # Increased from 4 to 5
    
    # Simulate mining process
    start_time = time.time()
    nonce = 0
    hash_found = None
    
    # Try to find a hash with required difficulty
    while time.time() - start_time < 5:  # Limit mining time to 5 seconds
        test_string = f"{challenge}{nonce}"
        test_hash = hashlib.sha256(test_string.encode()).hexdigest()
        
        if test_hash.startswith('0' * target_difficulty):
            hash_found = test_hash
            break
        nonce += 1
    
    if hash_found:
        # Calculate reward based on difficulty and time
        time_taken = time.time() - start_time
        base_reward = 0.0005  # Reduced from 0.001
        difficulty_bonus = target_difficulty * 0.0005
        time_bonus = max(0, (5 - time_taken) * 0.0001)
        
        coins_earned = base_reward + difficulty_bonus + time_bonus
        
        # Update user balance
        user_data["balance"] += coins_earned
        user_data["total_mined"] += coins_earned
        
        # Save updated user data
        redis_client.set(f"user:{current_user['username']}", json.dumps(user_data))
        
        # Update leaderboard
        redis_client.zadd("leaderboard", {current_user['username']: user_data["balance"]})
        
        # Add activity log entry
        add_activity(current_user['username'], "mine_online", coins_earned, f"Hash: {hash_found[:12]}...")

        return MiningResult(
            success=True,
            coins_earned=coins_earned,
            hash_found=hash_found,
            difficulty=target_difficulty
        )
    else:
        return MiningResult(
            success=False,
            coins_earned=0.0,
            hash_found="",
            difficulty=target_difficulty
        )

@app.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard():
    """Get the global leaderboard"""
    # Get top 50 users
    leaderboard_data = redis_client.zrevrange("leaderboard", 0, 49, withscores=True)
    
    leaderboard = []
    for rank, (username, balance) in enumerate(leaderboard_data, 1):
        # Get additional user data
        user_data = redis_client.get(f"user:{username}")
        if user_data:
            user_data = json.loads(user_data)
            leaderboard.append(LeaderboardEntry(
                username=username,
                balance=balance,
                total_mined=user_data.get("total_mined", 0.0),
                rank=rank
            ))
    
    return leaderboard

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        redis_client.ping()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
