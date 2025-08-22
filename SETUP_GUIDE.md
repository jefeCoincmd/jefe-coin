# 🚀 JEFE COIN - Quick Setup Guide

## Prerequisites
- Python 3.11+ installed
- Upstash Redis account (free at upstash.com)
- Render account (free at render.com)

## Step 1: Set Up Upstash Redis
1. Go to [upstash.com](https://upstash.com) and create a free account
2. Create a new Redis database
3. Copy your Redis URL, port, and password

## Step 2: Configure Environment
1. Create a `.env` file in the root directory
2. Add your Redis credentials:
```env
UPSTASH_REDIS_REST_URL=your-redis-url.upstash.io
UPSTASH_REDIS_REST_PORT=6379
UPSTASH_REDIS_REST_PASSWORD=your-redis-password
SECRET_KEY=your-random-secret-key
```

## Step 3: Local Development
1. Install dependencies:
   ```bash
   py -3.11 -m pip install -r requirements.txt
   ```

2. Start the server:
   ```bash
   # Windows
   start_server.bat
   
   # Or manually
   py -3.11 backend/main.py
   ```

3. Run the client:
   ```bash
   # Windows
   run_client.bat
   
   # Or manually
   py -3.11 client/crypto_client.py
   ```

4. Open the web leaderboard:
   - Open `frontend/index.html` in your browser

## Step 4: Deploy to Render
1. Push your code to GitHub
2. Go to [render.com](https://render.com) and create an account
3. Click "New +" → "Blueprint"
4. Connect your GitHub repository
5. Add environment variables in Render dashboard
6. Deploy!

## Step 5: Test Everything
Run the test script to verify your setup:
```bash
py -3.11 test_setup.py
```

## 🎮 How to Use
1. **Register** a new account in the client
2. **Login** with your credentials
3. **Start Mining** to earn cryptocurrency
4. **Check Balance** to see your earnings
5. **View Leaderboard** to compete with others

## 🆘 Troubleshooting
- **Server not starting**: Check your Redis credentials
- **Client can't connect**: Make sure server is running on port 8000
- **Mining not working**: Check your internet connection
- **Deployment issues**: Verify environment variables in Render

## 📞 Support
- Check the main README.md for detailed documentation
- Run `python test_setup.py` to diagnose issues
- Verify all environment variables are set correctly

Happy Mining! 🪙⛏️
