import requests
import json

base_url = "http://127.0.0.1:8001"

print("🔐 Testing Authentication API\n")

# Test 1: Login with correct credentials
print("1. Testing login with correct credentials...")
response = requests.post(
    f"{base_url}/api/auth/login",
    json={
        "username": "testuser",
        "password": "test123"
    }
)

print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Login successful!")
    print(f"   Token: {data['access_token'][:30]}...")
    print(f"   User: {data['user']['username']} ({data['user']['email']})")
    token = data['access_token']
else:
    print(f"   ❌ Login failed: {response.text}")
    token = None

# Test 2: Login with wrong password
print("\n2. Testing login with wrong password...")
response = requests.post(
    f"{base_url}/api/auth/login",
    json={
        "username": "testuser",
        "password": "wrongpassword"
    }
)
print(f"   Status: {response.status_code}")
if response.status_code == 401:
    print(f"   ✅ Correctly rejected: {response.json()['detail']}")
else:
    print(f"   ❌ Unexpected response: {response.text}")

# Test 3: Test chat endpoint with token
if token:
    print("\n3. Testing protected chat endpoint...")
    response = requests.post(
        f"{base_url}/api/chat",
        json={"message": "Hello!"},
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Chat endpoint accessible with token")
    else:
        print(f"   ❌ Failed: {response.text}")

print("\n✅ API tests complete!")
