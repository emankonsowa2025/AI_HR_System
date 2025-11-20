# backend/app.py
from fastapi import FastAPI
from backend.api.routes import router as api_router

app = FastAPI(title="AskTech - Dev Scaffold")
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8001, reload=True)

from backend.services.rag_manager import RAGManager
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(openai_api_key="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")
rag = RAGManager(embeddings)
print(rag.search("Python developer"))
