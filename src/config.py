"""Production-grade configuration management for MedVault RAG pipeline."""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings
from loguru import logger


class RAGConfig(BaseSettings):
    """MedVault RAG Configuration with validation."""
    
    # Paths
    vector_store_path: str = Field(default="vector_store", description="Path to vector database")
    data_path: str = Field(default="data/synthetic", description="Path to source documents")
    log_path: str = Field(default="logs", description="Path to log files")
    
    # Ollama Configuration
    ollama_base_url: str = Field(
        default="http://ollama:11434",
        description="Ollama service URL"
    )
    ollama_model: str = Field(
        default="mistral",
        description="Default LLM model name (mistral, llama3, neural-chat, etc.)"
    )
    ollama_timeout: int = Field(
        default=120,
        description="Timeout in seconds for Ollama requests"
    )
    ollama_max_retries: int = Field(
        default=3,
        description="Max retry attempts for Ollama connection"
    )
    
    # Embedding Configuration
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace embedding model"
    )
    embedding_batch_size: int = Field(
        default=32,
        description="Batch size for embedding generation"
    )
    
    # Retriever Configuration
    chunk_size: int = Field(
        default=1024,  # Increased from 500 for better context
        description="Document chunk size in characters"
    )
    chunk_overlap: int = Field(
        default=100,  # Increased from 50 for better coherence
        description="Character overlap between chunks"
    )
    
    # Retriever K values (hybrid search)
    retriever_k_bm25: int = Field(
        default=5,  # Increased from 3
        description="Number of BM25 (keyword) results"
    )
    retriever_k_vector: int = Field(
        default=5,  # Increased from 3
        description="Number of vector (semantic) results"
    )
    
    # Ensemble weights
    ensemble_weight_bm25: float = Field(
        default=0.35,
        description="Weight for BM25 retriever (0-1)"
    )
    ensemble_weight_vector: float = Field(
        default=0.65,
        description="Weight for vector retriever (0-1)"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    log_format: str = Field(
        default="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        description="Loguru format string"
    )
    
    # Production Settings
    enable_caching: bool = Field(
        default=True,
        description="Enable query result caching"
    )
    max_cache_size_mb: int = Field(
        default=500,
        description="Maximum cache size in MB"
    )
    persist_after_ingest: bool = Field(
        default=True,
        description="Automatically persist vector store after ingestion"
    )
    
    # Pydantic v2 configuration
    model_config = ConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra fields from .env file
    )
    
    @field_validator("ensemble_weight_bm25", "ensemble_weight_vector")
    @classmethod
    def validate_weights(cls, v):
        """Ensure weights are between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Weight must be between 0 and 1")
        return v
    
    @field_validator("chunk_size")
    @classmethod
    def validate_chunk_size(cls, v):
        """Ensure chunk size is reasonable."""
        if v < 100 or v > 5000:
            raise ValueError("Chunk size must be between 100 and 5000")
        return v
    
    def ensure_directories(self):
        """Create required directories if they don't exist."""
        for path in [self.vector_store_path, self.data_path, self.log_path]:
            Path(path).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {path}")
    
    def validate_weights_sum(self):
        """Validate that ensemble weights sum to 1.0 (with tolerance)."""
        total = self.ensemble_weight_bm25 + self.ensemble_weight_vector
        if not abs(total - 1.0) < 0.01:
            raise ValueError(
                f"Ensemble weights must sum to 1.0, got {total}. "
                f"BM25: {self.ensemble_weight_bm25}, Vector: {self.ensemble_weight_vector}"
            )


def get_config() -> RAGConfig:
    """Get configuration instance with validation."""
    config = RAGConfig()
    config.ensure_directories()
    config.validate_weights_sum()
    logger.info(f"Configuration loaded: Ollama={config.ollama_base_url}, Model={config.ollama_model}")
    return config


# Singleton instance
_config: Optional[RAGConfig] = None


def init_config(config_path: Optional[str] = None) -> RAGConfig:
    """Initialize and cache config."""
    global _config
    if config_path and os.path.exists(config_path):
        os.environ["MEDVAULT_ENV"] = config_path
    _config = get_config()
    return _config


def config() -> RAGConfig:
    """Get cached config instance."""
    global _config
    if _config is None:
        _config = init_config()
    return _config
