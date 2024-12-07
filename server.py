import socket
import requests

BASE_URL = "http://127.0.0.1:8080"  # Ensure this matches your Flask server's address and port

def test_register():
    # Test registering a new user
    data = {"username": "testuser", "email": "testuser@example.com"}
    response = requests.post(f"{BASE_URL}/register", json=data)
    if response.status_code == 201:
        print("Register Response:", response.json())
        return response.json()["password"]
    else:
        print("Registration failed:", response.json())
        return None

def test_auth(username, password):
    # Test authenticating a user
    data = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/auth", json=data)
    if response.status_code == 200:
        print("Auth Response:", response.json())
    else:
        print("Auth Failed:", response.json())

def test_rate_limit(username, password):
    # Test the rate limiter on /auth
    for i in range(12):  # Attempt 12 requests to trigger the rate limit
        print(f"Request {i + 1}:", end=" ")
        test_auth(username, password)

def main():
    password = test_register()
    if password:
        test_auth("testuser", password)
        print("\nTesting rate limit:")
        test_rate_limit("testuser", password)

if __name__ == "__main__":
    main()
    