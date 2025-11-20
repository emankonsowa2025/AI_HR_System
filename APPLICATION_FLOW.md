# AskTech HR Assistant - Application Flow

## 🎯 Navigation Flow

```
┌─────────────────┐
│  Welcome Page   │  (/)
│  Landing Screen │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│ Sign Up│ │  Sign In │
│/register│ │ /login   │
└────┬───┘ └────┬─────┘
     │          │
     └────┬─────┘
          ▼
   ┌──────────────┐
   │  Chat Page   │  (/chat)
   │ Main HR App  │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │Video Interview│
   │   (Modal)    │
   └──────────────┘
```

## 📁 File Structure

### Frontend Templates
- **`backend/Templates/welcome.html`** - New landing page with modern UI
- **`backend/Templates/login.html`** - User login page
- **`backend/Templates/register.html`** - User registration page
- **`backend/Templates/index.html`** - Main chat interface with video interview

### Static Assets
- **`backend/Static/app.js`** - Main JavaScript for chat and video interview
- **`backend/Static/style.css`** - Styles for all pages
- **`backend/Static/images/hr-assistant.jpg`** - Hero image (to be added)

### Alternative Frontend (Web)
- **`frontend/web/index.html`** - Standalone welcome screen
- **`frontend/web/style.css`** - Modern gradient styling
- **`frontend/web/app.js`** - Chat functionality

## 🚀 Application Routes

| Route | Purpose | File |
|-------|---------|------|
| `/` | Welcome/Landing page | `welcome.html` |
| `/login` | User authentication | `login.html` |
| `/register` | New user signup | `register.html` |
| `/chat` | Main HR assistant interface | `index.html` |

## 🎨 Features

### Welcome Page Features
- ✨ Animated gradient background with floating orbs
- 🖼️ Hero image showcasing AI HR Assistant
- 💼 Feature cards highlighting key capabilities
- 🔘 Call-to-action buttons (Get Started, Sign In)
- 📱 Fully responsive design

### Chat Interface Features
- 🤖 AI-powered HR assistance
- 🎥 Video interview modal
- 🎤 Speech recognition (Arabic & English)
- 🔊 Text-to-speech responses
- 📊 Career guidance and skills analysis
- 🎯 Job matching recommendations

## 🔧 Setup Instructions

### 1. Add the HR Assistant Image
Save the provided AI HR Assistant image as:
```
backend/Static/images/hr-assistant.jpg
```

### 2. Start the Application
```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run the server
python -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8001
```

### 3. Access the Application
Open your browser and navigate to:
```
http://127.0.0.1:8001/
```

## 📋 User Journey

1. **Landing Page** (`/`)
   - User sees the welcome screen with hero image
   - Options: "Get Started" (register) or "Sign In" (login)

2. **Authentication**
   - New users → Register page
   - Existing users → Login page
   - JWT token stored in localStorage

3. **Main Application** (`/chat`)
   - Protected route (requires authentication)
   - Access to chat interface
   - Video interview feature
   - Career guidance tools

## 🎯 Key Components

### Welcome Screen
- Professional hero section with AI assistant image
- Feature cards explaining capabilities
- Smooth animations and transitions
- Gradient background with floating orbs

### Chat Interface
- Real-time messaging with AI
- Message history
- Voice input/output
- Language selection (Arabic/English)
- User profile management

### Video Interview
- Modal-based interface
- Real-time video streaming
- Interactive Q&A session
- Transcript display
- Audio visualization

## 🔐 Authentication Flow

```javascript
// Check token on protected pages
const token = localStorage.getItem('access_token');
if (!token) {
    window.location.href = '/login';
}

// Login success
localStorage.setItem('access_token', token);
window.location.href = '/chat';

// Logout
localStorage.removeItem('access_token');
window.location.href = '/';
```

## 🎨 Design System

### Colors
- Primary: `#667eea` → `#764ba2` (Purple gradient)
- Secondary: `#f093fb` → `#f5576c` (Pink gradient)
- Accent: `#4facfe` → `#00f2fe` (Blue gradient)
- Success: `#43e97b` → `#38f9d7` (Green gradient)

### Typography
- Headings: `Poppins` (600, 700)
- Body: `Inter` (300, 400, 500, 600, 700)

### Spacing
- Small: `0.5rem` (8px)
- Medium: `1rem` (16px)
- Large: `2rem` (32px)
- XL: `3rem` (48px)

## 📱 Responsive Breakpoints

- Mobile: `< 768px`
- Tablet: `768px - 968px`
- Desktop: `> 968px`

## 🚀 Next Steps

1. ✅ Add HR Assistant image to `/static/images/`
2. ✅ Test the complete user flow
3. ✅ Verify authentication works
4. ✅ Test video interview functionality
5. ⚡ Optimize performance
6. 🎨 Fine-tune animations

## 💡 Tips

- The welcome page automatically redirects to login if not found
- All protected routes check for authentication token
- Video interview modal is triggered from the chat page
- Speech recognition works in Chrome, Edge (not Firefox)
- Arabic TTS uses Microsoft Hoda voice when available

---

**Built with ❤️ using FastAPI, Vanilla JS, and Modern CSS**
