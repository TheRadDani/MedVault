#!/usr/bin/env python3
"""
MedVault RAG Pipeline - Streamlit Web Application
Production-ready medical document analysis with encryption support
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag_engine import MedVaultRAG
from src.config import config as get_config
from src.encryption import get_encryption_manager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="MedVault RAG Pipeline",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 1.1rem;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def initialize_rag():
    """Initialize RAG pipeline once and cache it"""
    try:
        rag = MedVaultRAG()
        
        # Try to load existing vector store if available
        config = get_config()
        if os.path.exists(config.vector_store_path):
            logger.info(f"Loading existing vector store from {config.vector_store_path}")
            rag.load_existing(data_path=config.data_path)
        
        rag.health_check()
        return rag
    except Exception as e:
        st.error(f"Failed to initialize RAG pipeline: {str(e)}")
        logger.error(f"RAG initialization error: {e}")
        return None

def main():
    # Get configuration
    config = get_config()
    
    # Header
    st.title("🏥 MedVault RAG Pipeline")
    st.markdown("*Production-ready medical document analysis with encryption support*")
    
    # Initialize RAG
    rag = initialize_rag()
    
    if rag is None:
        st.error("""
        ⚠️ Failed to connect to RAG pipeline. Please ensure:
        - Ollama service is running on http://ollama:11434
        - Vector store is initialized
        - All dependencies are installed
        """)
        return
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # RAG Configuration
        st.subheader("RAG Settings")
        retriever_k = st.slider(
            "Number of documents to retrieve",
            min_value=1,
            max_value=10,
            value=config.retriever_k_bm25,
            help="Number of most relevant documents to return"
        )
        
        llm_temperature = st.slider(
            "LLM Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="Lower = more deterministic, Higher = more creative"
        )
        
        # Encryption status
        st.subheader("🔐 Security")
        encryption_manager = get_encryption_manager()
        encryption_status = "✅ Enabled" if encryption_manager.encryption_enabled else "⚠️ Disabled"
        st.info(f"Encryption: {encryption_status}")
        
        # Health check
        st.subheader("🩺 System Health")
        if st.button("Run Health Check"):
            try:
                health = rag.health_check()
                st.json(health)
            except Exception as e:
                st.error(f"Health check failed: {str(e)}")
    
    # Main content tabs
    tabs = st.tabs(["📝 Query Documents", "📊 Vector Store", "🔧 Data Management", "📚 Documentation"])
    
    # Tab 1: Query
    with tabs[0]:
        st.subheader("Query Medical Documents")
        
        query = st.text_area(
            "Enter your medical query:",
            placeholder="e.g., What medications were prescribed for patient with diabetes?",
            height=100
        )
        
        if st.button("🔍 Search", use_container_width=True):
            if query.strip():
                with st.spinner("Searching documents and generating response..."):
                    try:
                        answer, sources = rag.query(query, return_sources=True)
                        
                        # Display answer
                        st.subheader("📋 Answer")
                        st.markdown(answer)
                        
                        # Display sources
                        if sources:
                            st.subheader(f"📄 Source Documents ({len(sources)})")
                            for i, source in enumerate(sources, 1):
                                with st.expander(f"Source {i}: {source.metadata.get('source', 'Unknown')}"):
                                    st.text(source.page_content[:500] + "..." if len(source.page_content) > 500 else source.page_content)
                    except Exception as e:
                        st.error(f"Error during query: {str(e)}")
                        logger.error(f"Query error: {e}")
            else:
                st.warning("Please enter a query")
    
    # Tab 2: Vector Store
    with tabs[1]:
        st.subheader("Vector Store Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Load Existing Vector Store", use_container_width=True):
                try:
                    with st.spinner("Loading vector store..."):
                        result = rag.load_existing(data_path=config.data_path)
                    if result:
                        st.success("✅ Vector store loaded successfully")
                        st.cache_resource.clear()
                        st.info("🔄 Reloading RAG system...")
                        st.rerun()
                    else:
                        st.error("Failed to load vector store - check logs")
                except Exception as e:
                    st.error(f"Failed to load vector store: {str(e)}")
        
        with col2:
            if st.button("🔄 Reload Vector Store", use_container_width=True):
                try:
                    with st.spinner("Reloading vector store..."):
                        st.cache_resource.clear()
                    st.success("✅ Vector store reloaded")
                    st.info("🔄 Refreshing page...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to reload: {str(e)}")
    
    # Tab 3: Data Management
    with tabs[2]:
        st.subheader("📂 Data Management")
        
        st.markdown("""
        ### Ingest Documents
        Use the data generation and ingestion pipeline to add medical documents to your RAG system.
        """)
        
        ingest_option = st.radio(
            "Select ingestion method:",
            ["Plaintext Documents", "Encrypted Documents", "Generate Sample Data"]
        )
        
        if ingest_option == "Generate Sample Data":
            count = st.number_input("Number of synthetic records to generate:", min_value=1, max_value=1000, value=10)
            encrypt = st.checkbox("Encrypt generated data", value=True)
            
            if st.button("Generate & Ingest", use_container_width=True):
                try:
                    with st.spinner(f"Generating {count} medical records..."):
                        from src.data_generator import generate_dataset
                        encrypted_dir = str(Path(config.data_path) / "encrypted")
                        generate_dataset(
                            count=count,
                            encrypt=encrypt,
                            encrypted_output_dir=encrypted_dir
                        )
                    st.success("✅ Data generated successfully")
                    
                    if st.button("Ingest Generated Data", use_container_width=True):
                        with st.spinner("Ingesting data into RAG..."):
                            encrypted_dir = str(Path(config.data_path) / "encrypted")
                            ingest_path = encrypted_dir if encrypt else config.data_path
                            result = rag.ingest(encrypted_path=ingest_path if encrypt else None)
                        
                        if result:
                            st.success("✅ Data ingested successfully")
                            # Clear cache to reload RAG with new data
                            st.cache_resource.clear()
                            st.info("🔄 Reloading RAG system with new data...")
                            st.rerun()
                        else:
                            st.error("❌ Ingestion failed - check logs for details")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    logger.error(f"Data generation error: {e}")
        
        elif ingest_option == "Plaintext Documents":
            st.info("Upload plaintext .txt files for ingestion")
            # File uploader would go here in a full implementation
            
        elif ingest_option == "Encrypted Documents":
            st.info("Encrypted documents in encrypted/ directory will be automatically decrypted during ingestion")
    
    # Tab 4: Documentation
    with tabs[3]:
        st.subheader("📚 Documentation")
        
        st.markdown("""
        # MedVault RAG Pipeline Documentation
        
        ## Overview
        MedVault is a production-ready medical document analysis system using:
        - **LLM**: Ollama with Mistral model
        - **Vector Store**: ChromaDB for persistent storage
        - **Retrieval**: Hybrid search (BM25 + Dense embeddings)
        - **Security**: AES-128 encryption with PBKDF2 key derivation
        
        ## Quick Start
        1. Generate synthetic medical records
        2. Ingest documents into the vector store
        3. Query using natural language
        4. View source documents with citations
        
        ## Configuration
        See `.env.example` for all available configuration options.
        
        ## Security
        - Documents encrypted at rest using AES-128 Fernet
        - In-memory decryption during ingestion
        - HMAC-based tamper detection
        - HIPAA/GDPR compliant design
        
        For detailed information, see:
        - `PRODUCTION_GUIDE.md` - Production deployment guide
        - `ENCRYPTION_GUIDE.md` - Security and encryption details
        - `README.md` - General documentation
        """)

if __name__ == "__main__":
    main()
