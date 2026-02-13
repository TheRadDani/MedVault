"""MedVault RAG Pipeline - Clinical Document Q&A System."""

__version__ = "1.0.0"

from src.rag_engine import MedVaultRAG
from src.config import config, init_config
from src.logging_config import configure_logging
from src.data_generator import generate_dataset

__all__ = ["MedVaultRAG", "config", "init_config", "configure_logging", "generate_dataset"]
