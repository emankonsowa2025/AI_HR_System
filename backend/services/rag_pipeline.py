"""Core RAG pipeline implementation for processing and retrieving knowledge."""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.embeddings.base import Embeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

class RAGPipeline:
    """Manages the full RAG workflow: ingestion, indexing, and retrieval."""
    
    def __init__(
        self,
        embeddings: Embeddings,
        llm: Optional[ChatOpenAI] = None,
        index_path: Optional[Path] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        self.embeddings = embeddings
        self.llm = llm or ChatOpenAI(temperature=0.7)
        self.index_path = index_path or Path("knowledge_base.faiss")
        
        # Initialize text splitter for document chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        
        # Initialize or load vector store
        self.vectorstore = self._load_or_create_vectorstore()
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize retrieval chain
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(),
            memory=self.memory,
            verbose=True
        )
    
    def _load_or_create_vectorstore(self) -> FAISS:
        """Load existing vector store or create new one."""
        try:
            if self.index_path.exists():
                return FAISS.load_local(str(self.index_path), self.embeddings)
        except Exception as e:
            print(f"Error loading vector store: {e}")
        
        # Create new if loading fails
        return FAISS.from_texts(["Initial empty index"], self.embeddings)
    
    def add_documents(self, documents: List[Document], metadata: Optional[Dict[str, Any]] = None):
        """Process and add documents to the knowledge base."""
        # Split documents into chunks
        chunks = []
        for doc in documents:
            # Merge any existing metadata with new metadata
            doc_metadata = {**(metadata or {}), **(doc.metadata or {})}
            
            # Split the document
            doc_chunks = self.text_splitter.split_text(doc.page_content)
            
            # Create Document objects for each chunk
            chunks.extend([
                Document(
                    page_content=chunk,
                    metadata={
                        **doc_metadata,
                        'chunk_id': i,
                        'total_chunks': len(doc_chunks),
                        'ingested_at': datetime.utcnow().isoformat()
                    }
                )
                for i, chunk in enumerate(doc_chunks)
            ])
        
        # Add to vector store
        self.vectorstore.add_documents(chunks)
        
        # Save updated index
        self.save_index()
    
    def add_texts(self, texts: List[str], metadata: Optional[Dict[str, Any]] = None):
        """Add raw texts to the knowledge base."""
        documents = [Document(page_content=text, metadata=metadata) for text in texts]
        self.add_documents(documents)
    
    def query(
        self,
        question: str,
        chat_history: Optional[List[tuple[str, str]]] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query the knowledge base with context awareness."""
        
        # Prepare retrieval parameters
        search_kwargs = {}
        if metadata_filter:
            search_kwargs["filter"] = metadata_filter
        
        # Get response from QA chain
        response = self.qa_chain({
            "question": question,
            "chat_history": chat_history or []
        })
        
        # Get source documents for transparency
        source_documents = response.get("source_documents", [])
        sources = []
        for doc in source_documents:
            sources.append({
                "content": doc.page_content,
                "metadata": doc.metadata
            })
        
        return {
            "answer": response["answer"],
            "sources": sources,
            "chat_history": self.memory.chat_memory.messages
        }
    
    def save_index(self):
        """Save the vector store index to disk."""
        self.vectorstore.save_local(str(self.index_path))
    
    def load_index(self):
        """Load the vector store index from disk."""
        if self.index_path.exists():
            self.vectorstore = FAISS.load_local(str(self.index_path), self.embeddings)
            # Reinitialize retrieval chain with new vector store
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.vectorstore.as_retriever(),
                memory=self.memory,
                verbose=True
            )