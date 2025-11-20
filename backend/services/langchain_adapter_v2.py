# backend/services/langchain_adapter.py
from __future__ import annotations
from typing import List, Dict
import json
from datetime import datetime

# ---- LangChain modern imports ----
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
# ---- Internal imports ----
from backend.core.config import settings
from backend.db.db import get_connection
from backend.services.rag_manager import RAGManager
from backend.services.prompt_manager import prompt_manager


# =====================================================
# GLOBAL INITIALIZATIONS
# =====================================================

# Main chat model client (lazy initialization to handle missing API key)
chat = None
embeddings = None
rag_manager = None

def _ensure_openai_clients():
    """Lazy initialization of OpenAI clients - only when API key is available."""
    global chat, embeddings, rag_manager
    
    if not settings.is_openai_configured():
        raise ValueError(
            "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable "
            "or create a .env file in the backend directory with OPENAI_API_KEY=your_key_here"
        )
    
    if chat is None:
        chat = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY
        )
    
    if embeddings is None:
        embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
    
    if rag_manager is None:
        rag_manager = RAGManager(embeddings=embeddings)

# Text splitter for chunking longer content
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100
)

from backend.core.config import settings
embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)

# =====================================================
# ANALYZE SKILLS WITH AI
# =====================================================
def analyze_skills_with_ai(skills: List[str]) -> Dict:
    """
    Use the LLM to analyze given skills and suggest relevant job titles
    and technical interview questions.
    """
    _ensure_openai_clients()  # Ensure clients are initialized
    
    system_prompt = (
        "You are a career advisor and technical interviewer.\n"
        "Analyze the given skills and suggest:\n"
        "1. Suitable job titles ranked by relevance.\n"
        "2. Technical interview questions specific to these skills.\n"
        "Return response as JSON with 'titles' and 'questions' lists."
    )

    skill_list = ", ".join(skills)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Skills to analyze: {skill_list}")
    ]

    try:
        response = chat.invoke(messages)
        result = json.loads(response.content)
        return {
            "titles": result.get("titles", [])[:5],
            "questions": result.get("questions", [])[:5]
        }
    except json.JSONDecodeError:
        # fallback if model didn't return valid JSON
        return {"titles": [], "questions": []}
    except Exception as e:
        return {"error": str(e)}


# =====================================================
# RETRIEVE RELEVANT CHAT HISTORY
# =====================================================
def get_relevant_chat_history(query: str, limit: int = 3) -> List[str]:
    """Retrieve relevant past chat messages using vector similarity search."""
    try:
        results = rag_manager.search(query, k=limit)
        return [
            f"{doc.metadata['role']}: {doc.page_content} "
            f"({doc.metadata.get('created_at', 'unknown time')})"
            for doc in results
        ]
    except Exception as e:
        print(f"[RAGManager] Error retrieving history: {e}")
        return []


# =====================================================
# GENERATE CHAT RESPONSE
# =====================================================
def generate_chat_response(user_message: str) -> str:
    """
    Generate a contextual chat response that:
    - Uses retrieved conversation history
    - Adapts follow-up prompts based on detected skills
    - Provides detailed, actionable career advice
    """
    _ensure_openai_clients()  # Ensure clients are initialized

    # Retrieve context
    relevant_history = get_relevant_chat_history(user_message)
    context = "\n".join(relevant_history) if relevant_history else "No relevant history found."

    system_prompt = (
        "You are a career advisor and technical interviewer helping users with job-related questions.\n"
        "Use the provided chat history for context and follow these guidelines:\n"
        "1. If this is a new conversation, use an initial assessment prompt.\n"
        "2. When skills are mentioned, ask relevant follow-up questions.\n"
        "3. Guide users through skill assessment before making job suggestions.\n"
        "4. Give detailed, actionable advice specific to mentioned technologies.\n"
        "5. If appropriate, probe for experience level with specific skills."
    )

    # ---- Case 1: New conversation ----
    if not relevant_history:
        initial_prompt = prompt_manager.get_initial_prompt()
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"New conversation started. User said: {user_message}"),
            SystemMessage(content=f"Use this initial prompt: {initial_prompt}")
        ]
        response = chat.invoke(messages)
        return response.content

    # ---- Case 2: Existing conversation ----
    # Extract skills mentioned in conversation
    all_text = f"{context}\n{user_message}"
    skill_extraction_prompt = (
        "Extract any technical skills mentioned in the following text:\n"
        f"{all_text}\n"
        "List the skills as a comma-separated list."
    )