"""MedVault RAG Pipeline - Clinical Document Q&A System."""

__version__ = "1.0.0"

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    if name == "MedVaultRAG":
        from src.rag_engine import MedVaultRAG
        return MedVaultRAG
    elif name == "config":
        from src.config import config
        return config
    elif name == "init_config":
        from src.config import init_config
        return init_config
    elif name == "configure_logging":
        from src.logging_config import configure_logging
        return configure_logging
    elif name == "generate_dataset":
        from src.data_generator import generate_dataset
        return generate_dataset
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

def __dir__():
    return [
        "MedVaultRAG",
        "config",
        "init_config",
        "configure_logging",
        "generate_dataset",
        "EncryptionManager",
        "get_encryption_manager",
        "__version__"
    ]

# Import encryption directly (it has no heavy dependencies)
from src.encryption import EncryptionManager, get_encryption_manager

__all__ = [
    "MedVaultRAG",
    "config",
    "init_config",
    "configure_logging",
    "generate_dataset",
    "EncryptionManager",
    "get_encryption_manager"
]
