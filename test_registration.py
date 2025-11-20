from backend.db.database import SessionLocal
from backend.models.user import User
from backend.core.auth import get_password_hash

# Create a test user
db = SessionLocal()

# Check if user exists
existing = db.query(User).filter(User.username == "testuser").first()
if existing:
    print(f'User already exists: {existing.username}')
    db.delete(existing)
    db.commit()
    print('Deleted existing user')

# Create new user
hashed_password = get_password_hash("test123")
new_user = User(
    email="test@example.com",
    username="testuser",
    hashed_password=hashed_password
)

db.add(new_user)
db.commit()
db.refresh(new_user)

print(f'\n✅ User created successfully!')
print(f'   ID: {new_user.id}')
print(f'   Email: {new_user.email}')
print(f'   Username: {new_user.username}')
print(f'   Password Hash: {new_user.hashed_password[:30]}...')

# Test login
from backend.core.auth import verify_password
print(f'\n🔐 Testing login...')
print(f'   Correct password: {verify_password("test123", new_user.hashed_password)}')
print(f'   Wrong password: {verify_password("wrong", new_user.hashed_password)}')

db.close()
print('\n✅ Authentication system working!')
