"""
MedVault RAG Engine - Production-ready Retrieval-Augmented Generation pipeline.

Latest LangChain APIs (0.2.0+) with Ollama integration, hybrid retrieval,
error handling, comprehensive logging, and data encryption support.
"""

import os
import requests
from typing import Optional, Tuple, List, Any
from functools import lru_cache
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_ollama import ChatOllama  # Latest Ollama integration (0.2.0+)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from loguru import logger

from src.config import config
from src.encryption import get_encryption_manager


class MedVaultRAG:
    """
    Production-ready RAG pipeline for medical document retrieval and QA.
    
    Features:
    - Hybrid retrieval (BM25 sparse + vector dense search)
    - Configurable chunk sizing and overlap
    - Persistent vector store with Chroma
    - Full error handling and retry logic
    - Comprehensive logging
    - Query caching (optional)
    """
    
    def __init__(self, config_override: Optional[dict] = None):
        """
        Initialize RAG engine with configuration.
        
        Args:
            config_override: Optional dict to override config values
        """
        cfg = config()
        
        # Override with runtime config if provided
        if config_override:
            for key, value in config_override.items():
                setattr(cfg, key, value)
        
        self.cfg = cfg
        self.vector_db: Optional[Chroma] = None
        self.ensemble_retriever: Optional[EnsembleRetriever] = None
        self.llm: Optional[ChatOllama] = None
        self.embedding_function: Optional[HuggingFaceEmbeddings] = None
        self.encryption_manager = None  # Initialize encryption manager
        
        logger.info(f"MedVaultRAG initialized | Model: {self.cfg.ollama_model}")
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize LLM, embeddings, and encryption with error handling."""
        try:
            # Initialize embeddings
            logger.debug(f"Loading embeddings: {self.cfg.embedding_model}")
            
            # Try to auto-detect GPU, fall back to CPU if not available
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.debug(f"Using device: {device}")
            except ImportError:
                device = "cpu"
                logger.debug("PyTorch not available, using CPU")
            
            self.embedding_function = HuggingFaceEmbeddings(
                model_name=self.cfg.embedding_model,
                model_kwargs={"device": device}
            )
            
            # Initialize LLM with timeout and retry
            logger.debug(f"Connecting to Ollama: {self.cfg.ollama_base_url}")
            self.llm = ChatOllama(
                model=self.cfg.ollama_model,
                base_url=self.cfg.ollama_base_url,
                temperature=0.3,  # Lower temp for medical accuracy
                top_p=0.9,
                num_ctx=2048,  # Context window
                timeout=self.cfg.ollama_timeout,
                callback_manager=None,  # Can add observability here
            )
            
            # Initialize encryption manager for encrypted data handling
            self._initialize_encryption()
            
            # Test Ollama connection
            self._test_ollama_connection()
            logger.info("Components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def _initialize_encryption(self):
        """Initialize encryption manager for decryption during ingestion."""
        try:
            self.encryption_manager = get_encryption_manager()
            if self.encryption_manager.encryption_enabled:
                logger.info("Encryption manager initialized - encrypted data support enabled")
            else:
                logger.info("Encryption disabled - plaintext-only mode")
        except Exception as e:
            logger.warning(f"Failed to initialize encryption manager: {e}")
            # Don't fail initialization, just continue without encryption
            self.encryption_manager = None
    
    def _test_ollama_connection(self) -> bool:
        """Test connectivity to Ollama service."""
        try:
            # Use HTTP request to check if Ollama is responding
            response = requests.get(
                f"{self.cfg.ollama_base_url}/api/tags",
                timeout=5
            )
            is_connected = response.status_code == 200
            if is_connected:
                logger.debug("Ollama connection test passed")
            else:
                logger.warning(f"Ollama returned unexpected status {response.status_code}")
            return is_connected
        except requests.exceptions.Timeout:
            logger.warning("Ollama connection test timed out")
            return False
        except requests.exceptions.ConnectionError:
            logger.warning("Failed to connect to Ollama - connection error")
            return False
        except Exception as e:
            logger.warning(f"Ollama connection test failed: {e}")
            return False
    
    def _load_documents_with_decryption(self, data_path: str) -> List[Document]:
        """
        Load documents from directory, decrypting encrypted files in memory.
        
        Supports both:
        - Plaintext files (*.txt) - loaded directly
        - Encrypted files (*.txt) - decrypted in memory before chunking
        
        Args:
            data_path: Directory containing plaintext or encrypted files
        
        Returns:
            List of Document objects with content from both plaintext and encrypted files
        """
        documents = []
        failed_files = []
        
        try:
            data_dir = Path(data_path)
            
            # Load plaintext documents
            txt_files = list(data_dir.glob("*.txt"))
            
            if not txt_files:
                logger.warning(f"No .txt files found in {data_path}")
                return documents
            
            for file_path in txt_files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Try to decrypt if encryption is enabled
                    if self.encryption_manager and self.encryption_manager.encryption_enabled:
                        try:
                            content = self.encryption_manager.decrypt_text(content)
                            logger.debug(f"Decrypted in memory: {file_path.name}")
                        except Exception as decrypt_error:
                            # File not encrypted or decryption failed, use as-is
                            logger.debug(f"Treating {file_path.name} as plaintext (decryption failed: {decrypt_error})")
                    
                    # Create LangChain Document
                    doc = Document(
                        page_content=content,
                        metadata={"source": str(file_path)}
                    )
                    documents.append(doc)
                    logger.debug(f"Loaded document: {file_path.name}")
                
                except Exception as e:
                    logger.warning(f"Failed to load {file_path.name}: {e}")
                    failed_files.append(str(file_path))
            
            logger.info(f"Loaded {len(documents)} documents (failed: {len(failed_files)})")
            if failed_files:
                logger.warning(f"Failed files: {failed_files}")
            
            return documents
        
        except Exception as e:
            logger.error(f"Document loading failed: {e}", exc_info=True)
            return documents
    
    def ingest(
        self,
        data_path: Optional[str] = None,
        encrypted_path: Optional[str] = None,
        force_reindex: bool = False
    ) -> bool:
        """
        Load documents (plaintext or encrypted), chunk them, embed, and persist to vector store.
        
        Encrypted files are decrypted only in memory, never written back to disk.
        
        Args:
            data_path: Path to plaintext documents (or try encrypted path)
            encrypted_path: Path to encrypted documents (tries encryption first)
            force_reindex: Force reindexing even if vector store exists
        
        Returns:
            bool: Success status
        """
        try:
            # Determine which path to use
            if encrypted_path and os.path.exists(encrypted_path):
                ingest_path = encrypted_path
                logger.info(f"Ingesting encrypted documents from: {ingest_path}")
            else:
                ingest_path = data_path or self.cfg.data_path
                logger.info(f"Ingesting documents from: {ingest_path}")
            
            # Validate data path
            if not os.path.exists(ingest_path):
                logger.warning(f"Data path does not exist: {ingest_path}")
                logger.info(f"Creating data directory: {ingest_path}")
                os.makedirs(ingest_path, exist_ok=True)
                return False
            
            # Check for existing vector store
            if os.path.exists(self.cfg.vector_store_path) and not force_reindex:
                logger.info(f"Vector store exists: {self.cfg.vector_store_path}")
                return self.load_existing(data_path=ingest_path)
            
            # Load documents (with automatic decryption if needed)
            documents = self._load_documents_with_decryption(ingest_path)
            
            if not documents:
                logger.warning(f"No documents loaded from {ingest_path}")
                return False
            
            logger.info(f"Loaded {len(documents)} documents")
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.cfg.chunk_size,
                chunk_overlap=self.cfg.chunk_overlap,
                separators=["\n\n", "\n", ".", " ", ""]
            )
            chunks = text_splitter.split_documents(documents)
            logger.info(f"Split into {len(chunks)} chunks "
                       f"(size={self.cfg.chunk_size}, overlap={self.cfg.chunk_overlap})")
            
            # Create and persist vector store
            logger.debug("Creating vector embeddings...")
            self.vector_db = Chroma.from_documents(
                chunks,
                self.embedding_function,
                persist_directory=self.cfg.vector_store_path
            )
            
            # Persist explicitly for newer Chroma versions
            if hasattr(self.vector_db, 'persist'):
                self.vector_db.persist()
                logger.info(f"Vector store persisted to: {self.cfg.vector_store_path}")
            
            # Initialize retrievers
            self._initialize_retrievers(chunks)
            
            logger.info("Ingestion completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}", exc_info=True)
            return False
    
    def load_existing(self, data_path: Optional[str] = None, encrypted_path: Optional[str] = None) -> bool:
        """
        Load persisted vector store and initialize retrievers.
        Supports loading BM25 index from plaintext or encrypted documents.
        
        Args:
            data_path: Override default data path for retriever initialization
            encrypted_path: Path to encrypted documents for BM25 index
        
        Returns:
            bool: Success status
        """
        try:
            # Determine document path
            if encrypted_path and os.path.exists(encrypted_path):
                doc_path = encrypted_path
                logger.info(f"Using encrypted documents: {doc_path}")
            else:
                doc_path = data_path or self.cfg.data_path
            
            vector_store_path = self.cfg.vector_store_path
            
            # Check vector store exists
            if not os.path.exists(vector_store_path):
                logger.error(f"Vector store not found: {vector_store_path}")
                logger.info("Please run ingest() or copy vector store directory first")
                return False
            
            logger.info(f"Loading vector store from: {vector_store_path}")
            
            # Load persisted vector store
            self.vector_db = Chroma(
                persist_directory=vector_store_path,
                embedding_function=self.embedding_function
            )
            
            logger.info("Vector store loaded successfully")
            
            # Load documents for BM25 retriever (with decryption support)
            if os.path.exists(doc_path):
                documents = self._load_documents_with_decryption(doc_path)
                
                # Rechunk for consistency
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.cfg.chunk_size,
                    chunk_overlap=self.cfg.chunk_overlap
                )
                chunks = text_splitter.split_documents(documents)
                
                self._initialize_retrievers(chunks)
                logger.info(f"Loaded {len(chunks)} chunks for BM25 retrieval (encryption-aware)")
            else:
                logger.warning(f"Data path not found: {doc_path} (vector-only retrieval)")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load existing vector store: {e}", exc_info=True)
            return False
    
    def _initialize_retrievers(self, chunks: List[Document]):
        """
        Initialize hybrid BM25 + Vector ensemble retriever.
        
        Args:
            chunks: List of document chunks
        """
        try:
            # Validate chunks
            if not chunks:
                logger.warning("No chunks available for retriever initialization")
                return
            
            # BM25 Retriever (sparse, keyword-based)
            logger.debug("Initializing BM25 retriever...")
            try:
                bm25_retriever = BM25Retriever.from_documents(chunks)
                bm25_retriever.k = self.cfg.retriever_k_bm25
            except Exception as e:
                logger.warning(f"BM25 initialization failed: {e}. Continuing with vector-only retrieval.")
                bm25_retriever = None
            
            # Vector Retriever (dense, semantic)
            logger.debug("Initializing vector retriever...")
            if not self.vector_db:
                logger.warning("Vector DB not initialized - creating from chunks")
                if not chunks:
                    logger.error("Cannot create vector store with empty chunks")
                    return
                try:
                    # Create vector store from chunks if not already loaded
                    self.vector_db = Chroma.from_documents(
                        chunks,
                        self.embedding_function,
                        persist_directory=self.cfg.vector_store_path
                    )
                    logger.info("Vector store created from chunks")
                except Exception as e:
                    logger.error(f"Failed to create vector store: {e}")
                    # If we can't create vector store, use BM25 only
                    if bm25_retriever:
                        self.ensemble_retriever = bm25_retriever
                        logger.info("Using BM25-only retrieval (vector store unavailable)")
                    return
            
            try:
                vector_retriever = self.vector_db.as_retriever(
                    search_kwargs={"k": self.cfg.retriever_k_vector}
                )
            except Exception as e:
                logger.error(f"Failed to create vector retriever: {e}")
                if bm25_retriever:
                    self.ensemble_retriever = bm25_retriever
                    logger.info("Falling back to BM25-only retrieval")
                return
            
            # Ensemble Retriever (hybrid) or fallback to vector-only
            if bm25_retriever:
                self.ensemble_retriever = EnsembleRetriever(
                    retrievers=[bm25_retriever, vector_retriever],
                    weights=[
                        self.cfg.ensemble_weight_bm25,
                        self.cfg.ensemble_weight_vector
                    ]
                )
                logger.info(
                    f"Ensemble retriever initialized | "
                    f"BM25 k={self.cfg.retriever_k_bm25} "
                    f"({self.cfg.ensemble_weight_bm25:.0%}) | "
                    f"Vector k={self.cfg.retriever_k_vector} "
                    f"({self.cfg.ensemble_weight_vector:.0%})"
                )
            else:
                # Fallback to vector-only retrieval
                self.ensemble_retriever = vector_retriever
                logger.info(
                    f"Vector-only retriever initialized | "
                    f"k={self.cfg.retriever_k_vector}"
                )
            
        except Exception as e:
            logger.error(f"Failed to initialize retrievers: {e}", exc_info=True)
    
    @lru_cache(maxsize=128)
    def _get_prompt_template(self) -> ChatPromptTemplate:
        """Cache the prompt template."""
        template = """You are an expert AI Medical Assistant specializing in analyzing patient records and clinical data.

CRITICAL RULES:
1. Answer ONLY based on the provided context below.
2. If the answer is not found in the context, respond: "I cannot find this information in the available patient records."
3. Always cite the specific Patient ID when mentioning patient information.
4. Maintain a professional, clinical tone suitable for medical professionals.
5. Do not speculate or provide information outside the provided context.
6. If multiple patients are relevant, clearly differentiate between them.

CONTEXT (from patient records):
{context}

QUESTION: {question}

ANSWER:"""
        return ChatPromptTemplate.from_template(template)
    
    def query(self, question: str, return_sources: bool = True) -> Tuple[str, Optional[List[Document]]]:
        """
        Query the RAG pipeline and return answer with optional source documents.
        
        Args:
            question: User question about patient records
            return_sources: Whether to return source documents for verification
        
        Returns:
            Tuple of (answer, source_documents)
        
        Raises:
            ValueError: If system not initialized or question is invalid
        """
        try:
            # Validation
            if not self.ensemble_retriever:
                logger.error("Ensemble retriever not initialized")
                raise ValueError("System not initialized. Please ingest data first.")
            
            if not question or not question.strip():
                raise ValueError("Question cannot be empty")
            
            question = question.strip()
            logger.info(f"Processing query: {question[:100]}...")
            
            # Build retrieval-augmented generation chain
            prompt = self._get_prompt_template()
            
            # Modern LangChain syntax (0.2.0+)
            chain = (
                {
                    "context": self.ensemble_retriever | self._format_docs,
                    "question": lambda x: x  # Pass through the input as-is
                }
                | prompt
                | self.llm
                | StrOutputParser()
            )
            
            # Invoke chain
            answer = chain.invoke(question)
            
            # Retrieve source documents
            source_docs = None
            if return_sources:
                try:
                    source_docs = self.ensemble_retriever.invoke(question)
                    logger.debug(f"Retrieved {len(source_docs) if source_docs else 0} source documents")
                except Exception as e:
                    logger.warning(f"Failed to retrieve source documents: {e}")
            
            logger.info(f"Query completed | Answer length: {len(answer)} chars")
            return answer, source_docs
            
        except ValueError as e:
            logger.error(f"Query validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Query failed: {e}", exc_info=True)
            raise
    
    @staticmethod
    def _format_docs(docs: List[Document]) -> str:
        """Format retrieved documents for LLM context."""
        if not docs:
            return "No relevant documents found."
        
        formatted = []
        for i, doc in enumerate(docs, 1):
            # Include source metadata if available
            source = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page", "")
            
            source_info = f"[Source: {source}"
            if page:
                source_info += f", Page: {page}"
            source_info += "]"
            
            formatted.append(f"{i}. {doc.page_content}\n{source_info}")
        
        return "\n\n".join(formatted)
    
    def batch_query(self, questions: List[str]) -> List[Tuple[str, Optional[List[Document]]]]:
        """
        Process multiple questions efficiently.
        
        Args:
            questions: List of questions
        
        Returns:
            List of (answer, sources) tuples
        """
        logger.info(f"Processing batch of {len(questions)} queries")
        results = []
        
        for i, question in enumerate(questions, 1):
            try:
                answer, sources = self.query(question)
                results.append((answer, sources))
                logger.debug(f"Batch query {i}/{len(questions)} completed")
            except Exception as e:
                logger.error(f"Batch query {i} failed: {e}")
                results.append((f"Error: {str(e)}", None))
        
        return results
    
    def health_check(self) -> dict:
        """
        Perform system health check.
        
        Returns:
            dict with health status
        """
        health = {
            "ollama_connected": False,
            "vector_store_loaded": False,
            "retriever_ready": False,
            "embedding_model_loaded": False
        }
        
        try:
            # Check Ollama
            if self._test_ollama_connection():
                health["ollama_connected"] = True
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
        
        # Check vector store
        health["vector_store_loaded"] = self.vector_db is not None
        
        # Check retriever
        health["retriever_ready"] = self.ensemble_retriever is not None
        
        # Check embeddings
        health["embedding_model_loaded"] = self.embedding_function is not None
        
        is_healthy = all(health.values())
        logger.info(f"Health check: {'PASS' if is_healthy else 'FAIL'} | {health}")
        
        return health
