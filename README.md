# AskTech

AskTech — AI-powered recruitment assistant with RAG-based conversation context using NVIDIA AI.

## Features

- 🤖 **AI-Powered Chat**: Intelligent career advisor using NVIDIA Llama models
- 📚 **RAG System**: Context-aware responses using FAISS vector store
- 🎯 **Skills Analysis**: Technical skill assessment and job recommendations
- 💬 **Chat History**: Persistent conversation storage with semantic search
- 🔄 **Real-time Updates**: Background indexing of chat messages

## Repository Layout

- `backend/`: FastAPI backend with NVIDIA AI integration
- `frontend/`: React/Vite frontend (coming soon)
- `infra/`: Docker compose and deployment scripts

## Prerequisites

- Python 3.9+ (recommended: 3.11+)
- NVIDIA API Key (free at https://build.nvidia.com/)

## Quick Start

### 1. Clone and Setup Environment

```powershell
# Navigate to project directory
cd d:\asktech

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Configure NVIDIA API Key

1. Get your free API key:
   - Visit https://build.nvidia.com/
   - Sign in with your NVIDIA account
   - Click on any model to get your API key

2. Create `.env` file in project root:

```bash
# Copy the example
copy .env.example .env

# Edit with your key
notepad .env
```

3. Add your API key to `.env`:

```env
NVIDIA_API_KEY=nvapi-your-actual-key-here
NVIDIA_MODEL=nvidia/llama-3.1-nemotron-70b-instruct
NIM_BASE_URL=https://integrate.api.nvidia.com/v1
```

### 3. Run the Backend

```powershell
# Start the FastAPI server on port 8001
python -m uvicorn backend.app:app --reload --port 8001
```

The server will start at: http://127.0.0.1:8001

### 4. Test the API

**Using PowerShell:**

```powershell
# Test chat endpoint
Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/chat" -Method POST -ContentType "application/json" -Body '{"message":"hello"}'

# Test skills analysis
Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/skills" -Method POST -ContentType "application/json" -Body '{"user_id":"test","skills":["Python","FastAPI","LangChain"]}'

# Get chat history
Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/history" -Method GET
```

**Interactive API Docs:**

Open in your browser: http://127.0.0.1:8001/docs

## Project Structure

```
asktech/
├── backend/
│   ├── api/
│   │   └── routes.py          # API endpoints
│   ├── core/
│   │   └── config.py          # Configuration & settings
│   ├── db/
│   │   └── db.py              # SQLite database helpers
│   ├── models/
│   │   └── chat.py            # Pydantic models
│   ├── services/
│   │   ├── langchain_adapter.py    # NVIDIA AI integration
│   │   ├── rag_manager.py          # RAG & vector store
│   │   ├── chat_service.py         # Chat persistence
│   │   └── prompt_manager.py       # Prompt templates
│   ├── app.py                 # FastAPI application
│   └── requirements.txt       # Python dependencies
├── .env                       # Environment variables (create this!)
├── .env.example              # Example environment file
└── README.md                 # This file
```

## API Endpoints

### POST `/api/chat`
Send a chat message and get AI response.

**Request:**
```json
{
  "message": "What skills do I need for a backend developer role?"
}
```

**Response:**
```json
{
  "messages": [
    {
      "role": "assistant",
      "text": "For a backend developer role..."
    }
  ]
}
```

### POST `/api/skills`
Analyze skills and get job recommendations.

**Request:**
```json
{
  "user_id": "user123",
  "skills": ["Python", "FastAPI", "PostgreSQL"]
}
```

### GET `/api/history`
Retrieve chat history.

## Configuration

All configuration is managed through environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `NVIDIA_API_KEY` | Your NVIDIA API key (required for AI features) | None |
| `NVIDIA_MODEL` | NVIDIA model to use | `nvidia/llama-3.1-nemotron-70b-instruct` |
| `NIM_BASE_URL` | NVIDIA API base URL | `https://integrate.api.nvidia.com/v1` |
| `PROJECT_NAME` | Application name | `AskTech` |
| `SECRET_KEY` | Secret key for sessions | `default-secret-change-in-production` |
| `DATABASE_URL` | SQLite database path | `sqlite:///./asktech.db` |
| `PORT` | Server port | `8001` |

## Troubleshooting

### Server won't start
- Ensure virtual environment is activated
- Check if port 8001 is already in use
- Verify all dependencies are installed: `pip install -r backend/requirements.txt`

### 401 Unauthorized errors
- Check your NVIDIA_API_KEY is correct in `.env`
- Verify the key is not expired
- Get a new key from https://build.nvidia.com/

### Import errors
- Ensure you're running from the project root: `d:\asktech`
- Check Python version: `python --version` (should be 3.9+)
- Reinstall dependencies: `pip install -r backend/requirements.txt --upgrade`

## Development

### Running in Development Mode

```powershell
# With auto-reload
python -m uvicorn backend.app:app --reload --port 8001

# With custom port
$env:PORT = '8002'
python -m uvicorn backend.app:app --reload
```

### Running Tests

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=backend
```

## Production Deployment

See `infra/` directory for Docker and deployment configurations.

## License

MIT

## Support

For issues and questions:
- Check the troubleshooting section above
- Review API docs at http://127.0.0.1:8001/docs
- Visit https://build.nvidia.com/ for NVIDIA API support
````
3. Docker (optional)

```bash
docker compose up --build
```
