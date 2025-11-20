# backend/services/rag_manager.py
from __future__ import annotations
from typing import List, Optional
import json
from pathlib import Path
import threading
import time
from datetime import datetime

# LangChain imports
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Internal imports
from backend.db.db import get_connection
from backend.core.config import settings


class RAGManager:
    """Manages FAISS vector index for chat history, with background updating."""

    def __init__(
        self, 
        embeddings: Embeddings, 
        index_path: Optional[Path] = None,
        skip_initial_index: bool = False
    ):
        # Accept embeddings as argument (caller supplies it)
        self.embeddings = embeddings
        self.index_path = Path(index_path) if index_path else Path(__file__).parent / "chat_index"
        self.lock = threading.Lock()
        self.last_indexed_id = 0
        self.vectorstore = None

        # Create or load index (skip if requested to avoid startup errors)
        if not skip_initial_index:
            self._load_or_create_index()

        # Background indexing control
        self.should_run = True
        self.index_thread = threading.Thread(target=self._periodic_index, daemon=True)
        self.index_thread.start()

    # ------------------------------------------------------------------
    # Internal Index Handling
    # ------------------------------------------------------------------
    def _load_or_create_index(self):
        """Load existing FAISS index or create a new one."""
        with self.lock:
            try:
                # FAISS.save_local/load_local expect a directory; check for an indicator file
                if (self.index_path / "index.faiss").exists() or (self.index_path).exists():
                    self.vectorstore = FAISS.load_local(
                        str(self.index_path),
                        self.embeddings,
                        allow_dangerous_deserialization=True
                    )
                    meta_path = self.index_path.with_suffix(".meta")
                    if meta_path.exists():
                        with open(meta_path, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            self.last_indexed_id = meta.get("last_id", 0)
                    print(f"[RAGManager] Loaded existing FAISS index at {self.index_path}")
                else:
                    print(f"[RAGManager] Creating new FAISS index at {self.index_path}")
                    # FAISS.from_texts builds an index with the provided embeddings
                    self.vectorstore = FAISS.from_texts(["Initial empty index"], self.embeddings)
                    self._save_index()
            except Exception as e:
                print(f"[RAGManager] Error loading index: {e} → creating new one")
                try:
                    self.vectorstore = FAISS.from_texts(["Initial empty index"], self.embeddings)
                    self._save_index()
                except Exception as e2:
                    print(f"[RAGManager] Failed to create FAISS index: {e2}")
                    self.vectorstore = None

    def _save_index(self):
        """Save FAISS index and metadata atomically."""
        with self.lock:
            try:
                if self.vectorstore is not None:
                    self.vectorstore.save_local(str(self.index_path))
                meta_path = self.index_path.with_suffix(".meta")
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump({"last_id": self.last_indexed_id}, f)
            except Exception as e:
                print(f"[RAGManager] Error saving index: {e}")

    # ------------------------------------------------------------------
    # Background Updating
    # ------------------------------------------------------------------
    def _periodic_index(self, interval: int = 60):
        """Background thread to index new messages periodically."""
        while self.should_run:
            try:
                self.index_new_messages()
            except Exception as e:
                print(f"[RAGManager] Error during background indexing: {e}")
            time.sleep(interval)

    # ------------------------------------------------------------------
    # Main Indexing Logic
    # ------------------------------------------------------------------
    def index_new_messages(self):
        """Index new chat messages from DB (if any)."""
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, role, message, created_at FROM chats WHERE id > ? ORDER BY id",
                (self.last_indexed_id,)
            )
            new_messages = cur.fetchall()
            conn.close()
        except Exception as e:
            print(f"[RAGManager] DB error while fetching messages: {e}")
            return

        if not new_messages:
            return

        # Build document objects
        documents: List[Document] = []
        for msg in new_messages:
            doc = Document(
                page_content=str(msg[2]),
                metadata={
                    "id": msg[0],
                    "role": msg[1],
                    "created_at": str(msg[3])
                }
            )
            documents.append(doc)

        # Add to vector store
        with self.lock:
            try:
                if self.vectorstore is None:
                    # Try to create if missing
                    self.vectorstore = FAISS.from_texts([d.page_content for d in documents], self.embeddings)
                else:
                    self.vectorstore.add_documents(documents)
                self.last_indexed_id = new_messages[-1][0]
                self._save_index()
                print(f"[RAGManager] Indexed {len(new_messages)} new messages (up to ID {self.last_indexed_id})")
            except Exception as e:
                print(f"[RAGManager] Error indexing messages: {e}")

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    def search(self, query: str, k: int = 3) -> List[Document]:
        """Return top-k semantically similar past chat messages."""
        with self.lock:
            try:
                # Lazy initialization - create index if it doesn't exist
                if self.vectorstore is None:
                    print("[RAGManager] Vectorstore not initialized, attempting lazy initialization...")
                    self._load_or_create_index()
                
                # Ensure latest messages are indexed
                self.index_new_messages()
                
                if self.vectorstore is None:
                    print("[RAGManager] Warning: Vectorstore still None after initialization attempt")
                    return []
                    
                return self.vectorstore.similarity_search(query, k=k)
            except Exception as e:
                print(f"[RAGManager] Search error: {e}")
                return []
                return []

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------
    def shutdown(self):
        """Stop background thread and persist state."""
        self.should_run = False
        if hasattr(self, "index_thread") and self.index_thread.is_alive():
            self.index_thread.join(timeout=5)
        self._save_index()
        print("[RAGManager] Graceful shutdown complete")
