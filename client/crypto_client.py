import requests
import json
import time
import os
import sys
from datetime import datetime
from pathlib import Path
import secrets
import hashlib

from config import API_BASE_URL, REQUEST_TIMEOUT

# Path for local user data storage
USER_DATA_FILE = Path.home() / ".cryptosim_userdata.json"

class CryptoClient:
    def __init__(self, api_url=None):
        self.api_url = api_url or API_BASE_URL
        self.token = None
        self.username = None
        self.local_data = self.load_local_data()
        
    def load_local_data(self):
        """Load user data from the local JSON file."""
        if USER_DATA_FILE.exists():
            try:
                with open(USER_DATA_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_local_data(self):
        """Save user data to the local JSON file."""
        try:
            with open(USER_DATA_FILE, 'w') as f:
                json.dump(self.local_data, f, indent=4)
        except IOError:
            print("❌ Error: Could not save local user data.")
        
    def clear_screen(self):
        """Clear the command prompt screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def print_banner(self):
        """Print the application banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    💎 JEFE COIN 💎                    ║
║                   The Official JEFE COIN Client                  ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
        
    def check_server_status(self):
        """Check if the server is running"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        return False
        
    def register_user(self):
        """Register a new user"""
        print("\n" + "="*50)
        print("📝 USER REGISTRATION")
        print("="*50)
        
        username = input("Enter username: ").strip()
        if not username:
            print("❌ Username cannot be empty!")
            return False
            
        password = input("Enter password: ").strip()
        if not password:
            print("❌ Password cannot be empty!")
            return False
            
        confirm_password = input("Confirm password: ").strip()
        if password != confirm_password:
            print("❌ Passwords do not match!")
            return False
            
        try:
            response = requests.post(f"{self.api_url}/register", json={
                "username": username,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ Registration successful!")
                print(f"👤 Username: {data['username']}")
                print(f"💳 Wallet Address: {data['wallet_address']}")
                print(f"💰 Initial Balance: {data['balance']:.6f} $JEFE")
                return True
            else:
                error_data = response.json()
                print(f"❌ Registration failed: {error_data.get('detail', 'Unknown error')}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
            
    def login_user(self):
        """Login user"""
        print("\n" + "="*50)
        print("🔐 USER LOGIN")
        print("="*50)
        
        username = input("Enter username: ").strip()
        password = input("Enter password: ").strip()
        
        try:
            response = requests.post(f"{self.api_url}/login", json={
                "username": username,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['token']
                self.username = data['username']
                # Save session data for offline use
                self.local_data['username'] = self.username
                self.local_data['token'] = self.token
                if 'offline_proofs' not in self.local_data:
                    self.local_data['offline_proofs'] = []
                self.save_local_data()
                print(f"\n✅ Login successful! Welcome back, {self.username}!")
                return True
            else:
                error_data = response.json()
                print(f"❌ Login failed: {error_data.get('detail', 'Invalid credentials')}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
            
    def sync_offline_mining(self):
        """Sync offline mined coins with the server."""
        if not self.local_data.get('offline_proofs'):
            print("ℹ️ No offline activity to sync.")
            return

        print("\n" + "="*50)
        print("🔄 SYNCING OFFLINE ACTIVITY")
        print("="*50)
        print(f"Found {len(self.local_data['offline_proofs'])} proofs to sync. Connecting to server...")

        if not self.check_server_status():
            print("❌ Server is still offline. Cannot sync right now.")
            return

        try:
            headers = {"Authorization": f"Bearer {self.local_data.get('token')}"}
            payload = {"proofs": self.local_data['offline_proofs']}
            
            response = requests.post(f"{self.api_url}/sync", headers=headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Sync successful!")
                print(f"💰 $JEFE awarded: {data['total_coins_synced']:.6f}")
                print(f"💳 Your new balance is: {data['new_balance']:.6f}")
                # Clear local proofs after successful sync
                self.local_data['offline_proofs'] = []
                self.save_local_data()
            elif response.status_code == 401:
                print("❌ Your session has expired. Please log in again to sync.")
                # Clear the expired token
                self.local_data['token'] = None
                self.save_local_data()
            else:
                error_data = response.json()
                print(f"❌ Sync failed: {error_data.get('detail', 'Unknown server error')}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error during sync: {e}")
            
    def get_balance(self):
        """Get user's current balance"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.api_url}/balance", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print("\n" + "="*50)
                print("💰 WALLET BALANCE")
                print("="*50)
                print(f"👤 Username: {data['username']}")
                print(f"💳 Wallet Address: {data['wallet_address']}")
                print(f"💰 Current Balance: {data['balance']:.6f} $JEFE")
                print(f"⛏️  Total Mined: {data['total_mined']:.6f} $JEFE")
                print("="*50)
            else:
                print("❌ Failed to get balance!")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            
    def logout_user(self):
        """Logs out the user by invalidating the token on the server."""
        if self.token:
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                requests.post(f"{self.api_url}/logout", headers=headers, timeout=REQUEST_TIMEOUT)
            except requests.exceptions.RequestException:
                print("⚠️  Could not contact server to log out, but clearing local session.")

        # Clear local session regardless of server status
        self.token = None
        self.username = None
        if 'token' in self.local_data:
            self.local_data['token'] = None
        self.save_local_data()
        print("✅ Logged out successfully!")
        time.sleep(2)

    def send_coins(self):
        """Handles the process of sending coins to another user."""
        print("\n" + "="*50)
        print("💸 SEND COINS")
        print("="*50)

        recipient_address = input("Enter recipient's wallet address: ").strip()
        if not recipient_address:
            print("❌ Wallet address cannot be empty.")
            return

        try:
            amount_str = input("Enter amount to send: ").strip()
            amount = float(amount_str)
            if amount <= 0:
                print("❌ Amount must be a positive number.")
                return
        except ValueError:
            print("❌ Invalid amount. Please enter a number.")
            return
        
        # Confirmation prompt
        print(f"\nYou are about to send {amount:.6f} $JEFE to wallet {recipient_address[:10]}...")
        confirm = input("Are you sure? (y/n): ").strip().lower()
        if confirm != 'y':
            print("↪️ Transfer cancelled.")
            return

        print("🚀 Sending transaction...")
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "recipient_wallet_address": recipient_address,
                "amount": amount
            }
            response = requests.post(f"{self.api_url}/transfer", headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ Transfer successful!")
                print(f"Sent {amount:.6f} $JEFE to user '{data['recipient_username']}'.")
                print(f"💰 Your new balance is: {data['sender_new_balance']:.6f} $JEFE.")
            else:
                error_data = response.json()
                print(f"❌ Transfer failed: {error_data.get('detail', 'An unknown error occurred.')}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")

    def mine_crypto(self):
        """Start mining cryptocurrency (Online)"""
        if not self.token:
            print("❌ Please login first!")
            return
            
        print("\n" + "="*50)
        print("⛏️  MINING CRYPTOCURRENCY")
        print("="*50)
        print("🔍 Searching for valid hash...")
        print("⏱️  This may take a few seconds...")
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(f"{self.api_url}/mine", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    print(f"\n✅ Mining successful!")
                    print(f"💰 $JEFE earned: {data['coins_earned']:.6f}")
                    print(f"🔢 Hash found: {data['hash_found'][:16]}...")
                    print(f"🎯 Difficulty: {data['difficulty']} leading zeros")
                else:
                    print("\n❌ Mining failed - no valid hash found in time limit")
            else:
                print("❌ Mining request failed!")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
    
    def mine_offline(self):
        """Perform mining offline and store proof."""
        if not self.local_data.get('username'):
            print("❌ You must log in at least once while online to enable offline mining.")
            return

        print("\n" + "="*50)
        print("⛏️  MINING OFFLINE")
        print("="*50)
        print(f"👤 Mining for user: {self.local_data['username']}")
        print("🔍 Searching for valid hash (offline)...")

        # Simulate mining process locally
        challenge = secrets.token_hex(16)
        target_difficulty = 5  # Increased from 4 to 5, must match server
        start_time = time.time()
        nonce = 0
        hash_found = None

        # This can be a bit more intensive as it runs on user's machine
        while time.time() - start_time < 8:
            test_string = f"{challenge}{nonce}"
            test_hash = hashlib.sha256(test_string.encode()).hexdigest()
            
            if test_hash.startswith('0' * target_difficulty):
                hash_found = test_hash
                break
            nonce += 1
        
        if hash_found:
            proof = {
                "challenge": challenge,
                "nonce": nonce,
                "hash_found": hash_found,
                "difficulty": target_difficulty
            }
            if 'offline_proofs' not in self.local_data:
                self.local_data['offline_proofs'] = []
            
            self.local_data['offline_proofs'].append(proof)
            self.save_local_data()
            
            print(f"\n✅ Mining successful! Proof stored.")
            print(f"🔢 Hash: {hash_found[:16]}...")
            print(f"📦 You now have {len(self.local_data['offline_proofs'])} un-synced proofs.")
        else:
            print("\n❌ Mining failed - no valid hash found in time limit.")

    def show_leaderboard(self):
        """Show the global leaderboard"""
        try:
            response = requests.get(f"{self.api_url}/leaderboard")
            
            if response.status_code == 200:
                leaderboard = response.json()
                print("\n" + "="*70)
                print("🏆 GLOBAL LEADERBOARD")
                print("="*70)
                print(f"{'Rank':<5} {'Username':<20} {'Balance':<15} {'Total Mined':<15}")
                print("-" * 70)
                
                for entry in leaderboard[:20]:  # Show top 20
                    print(f"{entry['rank']:<5} {entry['username']:<20} {entry['balance']:<15.6f} {entry['total_mined']:<15.6f}")
                print("="*70)
            else:
                print("❌ Failed to load leaderboard!")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            
    def main_menu(self):
        """Display the main menu based on server status and login state."""
        is_server_up = self.check_server_status()

        while True:
            self.clear_screen()
            self.print_banner()
            
            # ATTEMPT TO SYNC ONCE WHEN SERVER IS FIRST DETECTED AS ONLINE
            if is_server_up and self.local_data.get('offline_proofs'):
                self.sync_offline_mining()
                input("\nPress Enter to continue...")
                self.clear_screen()
                self.print_banner()

            # --- ONLINE MENU ---
            if is_server_up:
                print("🟢 Server Status: ONLINE")
                if self.token:
                    print(f"👤 Logged in as: {self.username}")
                    print("\n📋 Available Actions:")
                    print("1. 💰 Check Balance")
                    print("2. ⛏️  Start Mining (Online)")
                    print("3. 💸 Send Coins")
                    print("4. 🏆 View Leaderboard")
                    print("5. 🚪 Logout")
                    print("6. ❌ Exit")
                    
                    choice = input("\nSelect an option (1-6): ").strip()
                    
                    if choice == "1":
                        self.get_balance()
                    elif choice == "2":
                        self.mine_crypto()
                    elif choice == "3":
                        self.send_coins()
                    elif choice == "4":
                        self.show_leaderboard()
                    elif choice == "5":
                        self.logout_user()
                    elif choice == "6":
                        print("👋 Thanks for using JEFE COIN!")
                        break
                    else:
                        print("❌ Invalid option!")
                else: # Server online, but not logged in
                    print("📋 Available Actions:")
                    print("1. 🔐 Login")
                    print("2. 📝 Register")
                    print("3. 🏆 View Leaderboard")
                    print("4. ❌ Exit")
                    
                    choice = input("\nSelect an option (1-4): ").strip()
                    if choice == "1":
                        self.login_user()
                    elif choice == "2":
                        self.register_user()
                    elif choice == "3":
                        self.show_leaderboard()
                    elif choice == "4":
                        print("👋 Thanks for using JEFE COIN!")
                        break
                    else:
                        print("❌ Invalid option!")
            
            # --- OFFLINE MENU ---
            else:
                print("🔴 Server Status: OFFLINE")
                if self.local_data.get('username'):
                    print(f"👤 Working offline as: {self.local_data['username']}")
                    offline_proofs_count = len(self.local_data.get('offline_proofs', []))
                    print(f"📦 Un-synced proofs: {offline_proofs_count}")

                    print("\n📋 Available Actions:")
                    print("1. ⛏️  Mine Offline")
                    print("2. 🔄 Attempt to Reconnect")
                    print("3. ❌ Exit")

                    choice = input("\nSelect an option (1-3): ").strip()
                    if choice == "1":
                        self.mine_offline()
                    elif choice == "2":
                        is_server_up = self.check_server_status()
                        if is_server_up:
                            print("✅ Server is back online!")
                            # The loop will now automatically trigger the sync process
                        else:
                            print("❌ Server is still offline.")
                        time.sleep(2)
                        continue # Re-render menu
                    elif choice == "3":
                        print("👋 Thanks for using JEFE COIN!")
                        break
                    else:
                        print("❌ Invalid option!")
                else: # Server offline, no local data
                    print("\nCannot connect to the server.")
                    print("Please connect to the internet and log in at least once to enable offline mode.")
                    print("\n📋 Available Actions:")
                    print("1. 🔄 Attempt to Reconnect")
                    print("2. ❌ Exit")
                    choice = input("\nSelect an option (1-2): ").strip()
                    if choice == "1":
                        is_server_up = self.check_server_status()
                    elif choice == "2":
                        print("👋 Thanks for using JEFE COIN!")
                        break
                    else:
                        print("❌ Invalid option!")

            input("\nPress Enter to continue...")


def main():
    """Main function"""
    client = CryptoClient()
    client.main_menu()

if __name__ == "__main__":
    main()
