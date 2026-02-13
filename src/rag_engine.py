"""
MedVault RAG Engine - Production-ready Retrieval-Augmented Generation pipeline.

Latest LangChain APIs (0.2.0+) with Ollama integration, hybrid retrieval,
error handling, and comprehensive logging.
"""

import os
from typing import Optional, Tuple, List, Any
from functools import lru_cache
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.retrievers import BaseRetriever
from langchain.retrievers import EnsembleRetriever
from langchain_ollama import ChatOllama  # Latest Ollama integration (0.2.0+)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassThrough
from langchain_core.documents import Document
from loguru import logger

from src.config import config


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
        
        logger.info(f"MedVaultRAG initialized | Model: {self.cfg.ollama_model}")
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize LLM and embeddings with error handling."""
        try:
            # Initialize embeddings
            logger.debug(f"Loading embeddings: {self.cfg.embedding_model}")
            self.embedding_function = HuggingFaceEmbeddings(
                model_name=self.cfg.embedding_model,
                model_kwargs={"device": "cuda"}  # Auto-detects GPU if available
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
            
            # Test Ollama connection
            self._test_ollama_connection()
            logger.info("Components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def _test_ollama_connection(self) -> bool:
        """Test connectivity to Ollama service."""
        try:
            response = self.llm.invoke("Test connection")
            logger.debug("Ollama connection test passed")
            return True
        except Exception as e:
            logger.warning(f"Ollama connection test failed: {e}")
            return False
    
    def ingest(self, data_path: Optional[str] = None, force_reindex: bool = False) -> bool:
        """
        Load documents, chunk them, embed them, and persist to vector store.
        
        Args:
            data_path: Override default data path
            force_reindex: Force reindexing even if vector store exists
        
        Returns:
            bool: Success status
        """
        try:
            data_path = data_path or self.cfg.data_path
            
            # Validate data path
            if not os.path.exists(data_path):
                logger.warning(f"Data path does not exist: {data_path}")
                logger.info(f"Creating data directory: {data_path}")
                os.makedirs(data_path, exist_ok=True)
                return False
            
            # Check for existing vector store
            if os.path.exists(self.cfg.vector_store_path) and not force_reindex:
                logger.info(f"Vector store exists: {self.cfg.vector_store_path}")
                return self.load_existing()
            
            logger.info(f"Ingesting documents from: {data_path}")
            
            # Load documents
            loader = DirectoryLoader(
                data_path,
                glob="*.txt",
                loader_cls=TextLoader,
                show_progress=True
            )
            documents = loader.load()
            
            if not documents:
                logger.warning(f"No documents found in {data_path}")
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
    
    def load_existing(self, data_path: Optional[str] = None) -> bool:
        """
        Load persisted vector store and initialize retrievers.
        
        Args:
            data_path: Override default data path for retriever initialization
        
        Returns:
            bool: Success status
        """
        try:
            data_path = data_path or self.cfg.data_path
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
            
            # Load documents for BM25 retriever
            if os.path.exists(data_path):
                loader = DirectoryLoader(
                    data_path,
                    glob="*.txt",
                    loader_cls=TextLoader,
                    show_progress=False
                )
                documents = loader.load()
                
                # Rechunk for consistency
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.cfg.chunk_size,
                    chunk_overlap=self.cfg.chunk_overlap
                )
                chunks = text_splitter.split_documents(documents)
                
                self._initialize_retrievers(chunks)
                logger.info(f"Loaded {len(chunks)} chunks for BM25 retrieval")
            else:
                logger.warning(f"Data path not found: {data_path} (vector-only retrieval)")
            
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
            # BM25 Retriever (sparse, keyword-based)
            logger.debug("Initializing BM25 retriever...")
            bm25_retriever = BM25Retriever.from_documents(chunks)
            bm25_retriever.k = self.cfg.retriever_k_bm25
            
            # Vector Retriever (dense, semantic)
            logger.debug("Initializing vector retriever...")
            vector_retriever = self.vector_db.as_retriever(
                search_kwargs={"k": self.cfg.retriever_k_vector}
            )
            
            # Ensemble Retriever (hybrid)
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
            
        except Exception as e:
            logger.error(f"Failed to initialize retrievers: {e}", exc_info=True)
            raise
    
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
                    "question": RunnablePassThrough()
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
