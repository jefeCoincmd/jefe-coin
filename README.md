# 💎 JEFE COIN 💎

The official client and server for JEFE COIN, a simulated cryptocurrency. Users can create accounts, mine JEFE COIN ($JEFE) by solving hash puzzles, and compete on a global leaderboard.

## 🌟 Features

- **User Management**: Register and login with secure password hashing
- **Wallet System**: Each user gets a unique wallet address
- **Mining Simulation**: Mine $JEFE by solving SHA-256 hash puzzles
- **Real-time Leaderboard**: Web-based leaderboard with live updates
- **Windows CLI Client**: The official JEFE COIN command prompt interface
- **Hardware-based Mining**: Mining difficulty adapts to your hardware
- **Secure API**: JWT-based authentication and secure endpoints

## 🏗️ Architecture

- **Backend**: FastAPI with Redis (Upstash) for data storage
- **Frontend**: Modern HTML/CSS/JS web interface
- **Client**: Python-based Windows command prompt application
- **Database**: Upstash Redis for scalable data storage
- **Hosting**: Render for free deployment

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Upstash Redis account (free tier available)
- Render account (free tier available)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd jefe-coin
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *If you have multiple Python versions, use `py -3.11 -m pip install -r requirements.txt`*

3. **Set up Upstash Redis**
   - Create a free account at [upstash.com](https://upstash.com)
   - Create a new Redis database
   - Note down your Redis URL, port, and password

4. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```env
   UPSTASH_REDIS_REST_URL=your-redis-url
   UPSTASH_REDIS_REST_PORT=your-redis-port
   UPSTASH_REDIS_REST_PASSWORD=your-redis-password
   SECRET_KEY=your-secret-key-here
   ```

5. **Start the backend server**
   ```bash
   # On Windows, simply run the batch file
   start_server.bat

   # Or manually
   py -3.11 backend/main.py
   ```
   The API will be available at `http://localhost:8000`

6. **Run the client application**
   ```bash
   # On Windows, simply run the batch file
   run_client.bat

   # Or manually
   py -3.11 client/crypto_client.py
   ```

7. **View the web leaderboard**
   Open `frontend/index.html` in your browser

## 🌐 Deployment to Render

### Automatic Deployment

1. **Connect your GitHub repository to Render**
   - Go to [render.com](https://render.com)
   - Create a new account or sign in
   - Click "New +" and select "Blueprint"
   - Connect your GitHub repository

2. **Configure environment variables in Render**
   - Go to your service dashboard
   - Navigate to "Environment" tab
   - Add the following environment variables:
     - `UPSTASH_REDIS_REST_URL`
     - `UPSTASH_REDIS_REST_PORT`
     - `UPSTASH_REDIS_REST_PASSWORD`
     - `SECRET_KEY` (Render will auto-generate this)

3. **Deploy**
   - Render will automatically detect the `render.yaml` file
   - It will deploy both the API and frontend services
   - Your application will be available at the provided URLs

### Manual Deployment

If you prefer manual deployment:

1. **Deploy the API**
   - Create a new Web Service
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables as mentioned above

2. **Deploy the Frontend**
   - Create a new Static Site
   - Set publish directory to `frontend`
   - Deploy

## 🎮 How to Use

### Windows Client

1. **Start the client**
   ```bash
   # On Windows, simply run the batch file
   run_client.bat
   ```

2. **Register a new account**
   - Choose option 2 (Register)
   - Enter username and password
   - You'll receive a wallet address

3. **Login and start mining**
   - Choose option 1 (Login)
   - Enter your credentials
   - Select option 2 (Start Mining)
   - Watch your $JEFE accumulate!

4. **Check your balance**
   - Select option 1 (Check Balance)
   - View your current balance and total mined

5. **View leaderboard**
   - Select option 3 (View Leaderboard)
   - See how you rank against other miners

### Web Leaderboard

- Open the web interface in your browser
- View real-time statistics and rankings
- The leaderboard updates automatically every 30 seconds
- Click "Refresh" for manual updates

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check and server status |
| `/register` | POST | Register a new user |
| `/login` | POST | Login user and get token |
| `/balance` | GET | Get user's wallet balance |
| `/mine` | POST | Start mining $JEFE |
| `/leaderboard` | GET | Get global leaderboard |
| `/health` | GET | Detailed health check |

## 🛠️ Technical Details

### Mining Algorithm

The mining process simulates real cryptocurrency mining:

1. **Challenge Generation**: Random 16-byte challenge is generated
2. **Hash Solving**: Client tries to find a nonce that produces a hash with 4 leading zeros
3. **Reward Calculation**: 
   - Base reward: 0.001 $JEFE
   - Difficulty bonus: 0.0005 × difficulty level
   - Time bonus: 0.0001 × (5 - time_taken)
4. **Hardware Adaptation**: Mining time is limited to 5 seconds to prevent resource abuse

### Security Features

- **Password Hashing**: bcrypt with salt
- **JWT Tokens**: Secure session management
- **Input Validation**: Pydantic models for data validation
- **CORS Protection**: Configured for web frontend
- **Rate Limiting**: Built into the mining algorithm

### Data Storage

- **User Data**: Stored in Redis with JSON serialization
- **Leaderboard**: Redis sorted set for efficient ranking
- **Sessions**: Redis with TTL for token management
- **Wallets**: Unique addresses with user mapping

## 📊 Performance

- **Mining Speed**: Limited to 5 seconds per attempt
- **Resource Usage**: Minimal CPU usage during mining
- **Scalability**: Redis-based architecture supports multiple users
- **Real-time Updates**: WebSocket-ready for live updates

## 🔮 Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] Transaction system between users
- [ ] Mining difficulty adjustment
- [ ] Mobile app support
- [ ] Advanced statistics and charts
- [ ] Mining pools and collaboration
- [ ] NFT integration
- [ ] Blockchain simulation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues:

1. Check the server logs for errors
2. Verify your Upstash Redis connection
3. Ensure all environment variables are set correctly
4. Check that the API is running and accessible

## 🎯 Demo

Try the live demo:
- **API**: [Your Render API URL]
- **Frontend**: [Your Render Frontend URL]
- **Client**: Download and run locally

---

**Happy Mining! 💎⛏️**
