# Quick Start - AskTech with Authentication

## Starting the Server

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Start the server
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8001
```

The browser will automatically open at http://127.0.0.1:8001/ and redirect to the login page.

## First Time Setup

1. **Register a new account**:
   - Click "إنشاء حساب جديد" (Create new account)
   - Enter your email, username, and password
   - Click "إنشاء الحساب" (Create Account)
   - You'll be automatically logged in and redirected to chat

2. **Use the chat**:
   - Type or speak your questions in Arabic or English
   - Switch language using the dropdown
   - The assistant will respond in text and speech

3. **Logout**:
   - Click "خروج" (Logout) button in the top right
   - Confirm to logout

## Default Users

The database starts empty. You need to register the first user through the web interface.

## Testing Authentication

### Test Registration:
```powershell
# Using PowerShell
$body = @{
    email = "test@example.com"
    username = "testuser"
    password = "password123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/auth/register" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

### Test Login:
```powershell
$body = @{
    username = "testuser"
    password = "password123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/auth/login" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

# Save the token
$token = $response.access_token
Write-Host "Token: $token"
```

### Test Protected Chat Endpoint:
```powershell
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$body = @{
    message = "Hello!"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/chat" `
    -Method POST `
    -Headers $headers `
    -Body $body
```

## Features

✅ User registration with email validation
✅ Secure login with JWT tokens (30-day expiration)
✅ Password hashing with bcrypt
✅ Protected chat endpoints
✅ Automatic authentication checks
✅ Logout functionality
✅ Bilingual UI (Arabic/English)
✅ Speech input/output in both languages
✅ User info display
✅ Session persistence with localStorage

## Database

- Location: `asktech.db` (SQLite)
- Contains `users` table with encrypted passwords
- Automatically created on first server start

## Environment Variables

Optional `.env` configuration:

```env
# Secret key for JWT tokens (change in production!)
SECRET_KEY=your-secret-key-change-this-in-production-12345678

# Database URL
DATABASE_URL=sqlite:///./asktech.db

# OpenAI API Key (for chat functionality)
OPENAI_API_KEY=sk-your-key-here
```

## Troubleshooting

### Can't access chat page
- Make sure you're logged in
- Check browser localStorage for `access_token`
- Try logging in again

### Token expired
- Tokens expire after 30 days
- Simply login again to get a new token

### Forgot password
- Currently no password reset feature
- You can manually delete the user from the database and re-register

### Database issues
- Delete `asktech.db` file to start fresh
- Server will recreate it on next start

## Security Notes

⚠️ **Important for Production:**

1. Change the `SECRET_KEY` in `.env` to a secure random string
2. Use HTTPS in production
3. Consider shorter token expiration times
4. Add rate limiting to prevent brute force attacks
5. Implement password reset functionality
6. Add email verification
7. Consider adding 2FA for sensitive accounts

## API Endpoints

### Public (No Auth):
- `GET /` - Redirects to login
- `GET /login` - Login page
- `GET /register` - Registration page
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user

### Protected (Requires JWT):
- `GET /chat` - Chat interface
- `POST /api/chat` - Send chat message
- `GET /api/history` - Get chat history
- `GET /api/auth/me` - Get current user info

## Need Help?

Check `AUTHENTICATION_GUIDE.md` for detailed implementation details.
