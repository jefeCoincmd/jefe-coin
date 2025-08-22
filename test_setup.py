#!/usr/bin/env python3
"""
Test script to verify CryptoSim setup
"""

import requests
import json
import time
import sys

def test_server_connection(api_url="http://localhost:8000"):
    """Test if the server is running and accessible"""
    print("🔍 Testing server connection...")
    try:
        response = requests.get(f"{api_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and accessible")
            return True
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def test_registration(api_url="http://localhost:8000"):
    """Test user registration"""
    print("\n📝 Testing user registration...")
    test_user = {
        "username": f"testuser_{int(time.time())}",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{api_url}/register", json=test_user)
        if response.status_code == 200:
            data = response.json()
            print("✅ Registration successful")
            print(f"   Username: {data['username']}")
            print(f"   Wallet: {data['wallet_address']}")
            return data
        else:
            print(f"❌ Registration failed: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Registration error: {e}")
        return None

def test_login(api_url="http://localhost:8000", user_data=None):
    """Test user login"""
    if not user_data:
        print("❌ No user data for login test")
        return None
        
    print("\n🔐 Testing user login...")
    login_data = {
        "username": user_data["username"],
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{api_url}/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful")
            print(f"   Token received: {len(data['token'])} characters")
            return data['token']
        else:
            print(f"❌ Login failed: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Login error: {e}")
        return None

def test_balance(api_url="http://localhost:8000", token=None):
    """Test balance retrieval"""
    if not token:
        print("❌ No token for balance test")
        return False
        
    print("\n💰 Testing balance retrieval...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{api_url}/balance", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Balance retrieval successful")
            print(f"   Balance: {data['balance']:.6f} coins")
            print(f"   Total mined: {data['total_mined']:.6f} coins")
            return True
        else:
            print(f"❌ Balance retrieval failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Balance error: {e}")
        return False

def test_mining(api_url="http://localhost:8000", token=None):
    """Test mining functionality"""
    if not token:
        print("❌ No token for mining test")
        return False
        
    print("\n⛏️  Testing mining functionality...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(f"{api_url}/mine", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print("✅ Mining successful")
                print(f"   Coins earned: {data['coins_earned']:.6f}")
                print(f"   Hash found: {data['hash_found'][:16]}...")
                print(f"   Difficulty: {data['difficulty']}")
            else:
                print("⚠️  Mining failed (no hash found in time limit)")
            return True
        else:
            print(f"❌ Mining failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Mining error: {e}")
        return False

def test_leaderboard(api_url="http://localhost:8000"):
    """Test leaderboard functionality"""
    print("\n🏆 Testing leaderboard...")
    
    try:
        response = requests.get(f"{api_url}/leaderboard")
        if response.status_code == 200:
            data = response.json()
            print("✅ Leaderboard retrieval successful")
            print(f"   Number of users: {len(data)}")
            if data:
                print(f"   Top user: {data[0]['username']} with {data[0]['balance']:.6f} coins")
            return True
        else:
            print(f"❌ Leaderboard failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Leaderboard error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 CryptoSim Setup Test")
    print("=" * 50)
    
    # Get API URL from command line or use default
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    print(f"Testing API at: {api_url}")
    
    # Run tests
    tests_passed = 0
    total_tests = 5
    
    if test_server_connection(api_url):
        tests_passed += 1
        
        user_data = test_registration(api_url)
        if user_data:
            tests_passed += 1
            
            token = test_login(api_url, user_data)
            if token:
                tests_passed += 1
                
                if test_balance(api_url, token):
                    tests_passed += 1
                    
                if test_mining(api_url, token):
                    tests_passed += 1
                    
        if test_leaderboard(api_url):
            tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Your CryptoSim setup is working correctly.")
        print("\nNext steps:")
        print("1. Run the client: python client/crypto_client.py")
        print("2. Open the web leaderboard: frontend/index.html")
        print("3. Start mining and competing!")
    else:
        print("⚠️  Some tests failed. Please check your setup:")
        print("1. Make sure the server is running: python backend/main.py")
        print("2. Verify your Upstash Redis connection")
        print("3. Check your environment variables")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
