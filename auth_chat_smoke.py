import requests

BASE_URL = "http://127.0.0.1:8001"
USERNAME = "testuser"
PASSWORD = "test123"
EMAIL = "test@example.com"

print("🔎 Running auth + chat smoke test\n")

def post(path: str, json=None, headers=None):
    return requests.post(f"{BASE_URL}{path}", json=json, headers=headers or {})

# Try login first
print("1) Login attempt...")
login = post("/api/auth/login", {"username": USERNAME, "password": PASSWORD})
if login.status_code == 200:
    data = login.json()
    token = data["access_token"]
    print(f"   ✅ Logged in as {data['user']['username']} ({data['user']['email']})")
else:
    print(f"   ℹ️  Login failed ({login.status_code}). Trying register...")
    reg = post("/api/auth/register", {"email": EMAIL, "username": USERNAME, "password": PASSWORD})
    if reg.status_code in (200, 201):
        data = reg.json()
        token = data["access_token"]
        print(f"   ✅ Registered + logged in as {data['user']['username']} ({data['user']['email']})")
    else:
        print(f"   ❌ Register failed: {reg.status_code} {reg.text}")
        token = None

# Chat
if token:
    print("\n2) Calling /api/chat with Bearer token...")
    chat = post("/api/chat", {"message": "Hello!"}, headers={"Authorization": f"Bearer {token}"})
    print(f"   Status: {chat.status_code}")
    if chat.status_code == 200:
        try:
            data = chat.json()
            msgs = data.get("messages", [])
            if msgs:
                print(f"   ✅ Chat OK: {msgs[0].get('text', '')[:80]}...")
            else:
                print("   ⚠️ No messages returned")
        except Exception:
            print(f"   ⚠️ Non-JSON response: {chat.text[:200]}...")
    else:
        print(f"   ❌ Chat error: {chat.status_code} {chat.text}")
else:
    print("\n⚠️ Skipping chat test due to missing token.")

print("\n✅ Done")
