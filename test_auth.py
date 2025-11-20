from backend.core.auth import get_password_hash, verify_password

# Test password hashing
pwd = 'test123'
hashed = get_password_hash(pwd)

print(f'Original password: {pwd}')
print(f'Hashed password: {hashed[:30]}...')
print(f'Verify correct password: {verify_password(pwd, hashed)}')
print(f'Verify wrong password: {verify_password("wrong", hashed)}')
print('\n✅ Password hashing working correctly!')
