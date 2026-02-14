# MedVault - Production-Ready Medical RAG Pipeline

A comprehensive, GPU-accelerated Retrieval-Augmented Generation (RAG) pipeline for medical document analysis with enterprise-grade security and deployment tools.

## ✨ Key Features

- **🚀 GPU Acceleration:** NVIDIA CUDA support with RTX 4090 detected and optimized
- **🔐 Encryption at Rest:** AES-128 Fernet encryption with PBKDF2 key derivation (100k iterations)  
- **🏥 Medical-Grade:** HIPAA-aligned architecture, structured logging, comprehensive health checks
- **🐳 Containerized:** Multi-stage Docker builds, non-root execution, full docker-compose orchestration
- **⚡ Hybrid Retrieval:** BM25 sparse search + dense embeddings with 35/65 ensemble weighting
- **🔄 Latest APIs:** LangChain 0.2.0+, Ollama latest stable, sentence-transformers 2.7.0+
- **📊 Production-Ready:** Error handling, graceful degradation, detailed monitoring

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              Streamlit Web Interface                          │
│           (http://localhost:8501)                            │
├──────────────────────────────────────────────────────────────┤
│                   MedVault RAG Engine                        │
│  ┌────────────────────────┬─────────────────────────────┐  │
│  │  Encryption Module     │  Configuration Management  │  │
│  │  (AES-128 Fernet)      │  (Pydantic validated)      │  │
│  └────────────────────────┴─────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐    │
│  │      Hybrid Retrieval (35% BM25 + 65% Dense)      │    │
│  │  - BM25: rank-bm25 keyword search                  │    │
│  │  - Dense: sentence-transformers embeddings         │    │
│  │  - Ensemble: weighted combination                  │    │
│  └────────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────────┤
│              ChromaDB Vector Store                           │
│         (Persistent /vector_store/)                         │
├──────────────────────────────────────────────────────────────┤
│         Ollama LLM Inference Engine                          │
│  - Models: Mistral, Llama2, Neural Chat, Phi                │
│  - GPU: Auto-detected and optimized                         │
│  - Streaming: Enabled for real-time responses               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites Check

```bash
docker --version      # Should be 20.10+
docker-compose --version  # Should be 1.28+
nvidia-smi           # Optional: check GPU availability
```

### 1. Clone Repository

```bash
git clone https://github.com/TheRadDani/MedVault.git
cd MedVault
```

### 2. Configure (Optional)

```bash
cp .env.example .env
# Edit .env if needed for custom settings
```

### 3. Build & Start

```bash
# Build Docker image
docker-compose build app

# Start services
docker-compose up -d

# Verify services
docker-compose ps
```

### 4. Pull LLM Model

```bash
# Pull Mistral (4.1GB, recommended)
docker-compose exec ollama ollama pull mistral

# Or: llama2, neural-chat, phi
```

### 5. Open Application

```bash
# Open browser to:
http://localhost:8501
```

✅ **Done! Start generating medical insights.**

---

## 📖 Detailed Build Instructions

### System Requirements

| Level | RAM | GPU VRAM | Disk | Docker |
|-------|-----|----------|------|--------|
| Minimum | 16GB | 4GB | 30GB | 20.10+ |
| Recommended | 32GB | 16GB | 100GB SSD | 24.0+ |
| Optimal | 64GB | 24GB RTX4090 | 500GB NVMe | 24.0+ |

### Step-by-Step Build

#### Step 1: Verify Environment

```bash
# Check Docker installation
docker run hello-world

# Check GPU support (optional)
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi

# Check disk space
df -h | grep -E "/$|/home"  # Need 30GB+
```

#### Step 2: Clone and Configure

```bash
# Clone repository
git clone https://github.com/yourusername/MedVault.git
cd MedVault

# Verify structure
ls -la  # Should see: app/, src/, docker-compose.yml, Dockerfile, etc.

# Copy configuration
cp .env.example .env

# Optionally set encryption
# Edit .env and add ENCRYPTION_KEY or ENCRYPTION_PASSWORD
```

#### Step 3: Build Docker Image

```bash
# Build app image (takes 5-10 minutes)
docker-compose build app

# Shows progress:
# #1 [internal] load build definition  
# #2 [python:3.11-slim] resolved          
# ... downloading dependencies ...
# #12 [stage-1 6/6] Successfully built ...

# Verify image created
docker images | grep medvault_app
```

#### Step 4: Start Services

```bash
# Start in background
docker-compose up -d

# Watch startup (Ctrl+C anytime, services stay running)
docker-compose logs -f

# Expected indicators:
# ollama | Listening on [::]:11434 (version 0.16.1)
# app | You can now view your Streamlit app in your browser.
```

#### Step 5: Verify Services

```bash
# Check status
docker-compose ps

# Should show both "Up (healthy)":
# NAME            STATUS              PORTS
# medvault_app    Up (healthy)        0.0.0.0:8501->8501/tcp
# medvault_ollama Up (healthy)        0.0.0.0:11434->11434/tcp

# Test Ollama API
curl http://localhost:11434/api/tags

# Test Streamlit
curl -s http://localhost:8501 | head -5
```

#### Step 6: Download LLM Model

```bash
# Pull Mistral model (recommended, ~4GB)
docker-compose exec ollama ollama pull mistral

# Wait for completion:
# pulling manifest...
# pulling <hash>... done

# List available models
docker-compose exec ollama ollama list
```

#### Step 7: Access Application

```bash
# Via browser
open http://localhost:8501         # macOS
xdg-open http://localhost:8501     # Linux  
start http://localhost:8501        # Windows

# Or via curl
curl http://localhost:8501
```

---

## 💡 Usage Examples

### Generate Sample Data

```python
from src.data_generator import generate_dataset

# Generate 50 encrypted medical records
generate_dataset(
    count=50,
    encrypt=True,
    encryption_password="secure-password",
    encrypted_output_dir="data/encrypted"
)
```

### Ingest & Query

```python
from src.rag_engine import MedVaultRAG

# Initialize RAG
rag = MedVaultRAG()

# Ingest encrypted documents (transparent decryption)
rag.ingest(encrypted_path="data/encrypted")

# Query with source documents
answer, sources = rag.query(
    "What medications were prescribed?",
    return_sources=True
)

print(answer)
for doc in sources:
    print(f"Source: {doc.metadata['source']}")
```

### Batch Processing

```python
questions = [
    "What is the diagnosis?",
    "Which medications were prescribed?",
    "What are next steps?",
]

results = rag.batch_query(questions)
for q, a in zip(questions, results):
    print(f"{q}\n{a}\n")
```

---

## 🔒 Encryption Setup

### Key-Based (Recommended)

```bash
# Generate key
python -c "from src.encryption import EncryptionManager; print(EncryptionManager.generate_key())"

# Output: gAAAAABl...base64-encoded-key...

# Add to .env
echo "ENCRYPTION_KEY=gAAAAABl..." >> .env
```

### Password-Based

```bash
# Add to .env  
echo "ENCRYPTION_PASSWORD=my-secure-password" >> .env
```

### Verify Encryption

```bash
python test_encryption.py
# ✅ All encryption tests passed!
```

See [ENCRYPTION_GUIDE.md](ENCRYPTION_GUIDE.md) for detailed security setup.

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama service endpoint |
| `OLLAMA_MODEL` | `mistral` | Default LLM model |
| `CHUNK_SIZE` | `1024` | Document chunk size |
| `RETRIEVER_K_BM25` | `5` | BM25 results count |
| `ENSEMBLE_WEIGHT_BM25` | `0.35` | BM25 weight (0-1) |
| `ENCRYPT_DATA_AT_REST` | `false` | Enable encryption |
| `ENCRYPTION_KEY` | (empty) | Encryption key (Fernet) |
| `ENCRYPTION_PASSWORD` | (empty) | Password for key derivation |

### Resource Limits

Edit `docker-compose.yml` for your system:

```yaml
services:
  ollama:
    cpus: '4.0'
    mem_limit: 16g
    
  app:
    cpus: '2.0'
    mem_limit: 8g
```

---

## 🐛 Troubleshooting

### GPU Not Detected

```bash
# Test GPU availability
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi

# Check Ollama logs
docker logs medvault_ollama | grep -i "cuda\|gpu"

# Solution: Install nvidia-docker2
# See: https://github.com/NVIDIA/nvidia-docker
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8501

# Kill it
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Out of Memory

```bash
# Check memory usage
docker stats medvault_ollama medvault_app

# Solutions:
# 1. Reduce OLLAMA_NUM_PARALLEL in .env  
# 2. Use smaller model (phi instead of mistral)
# 3. Increase system RAM/swap
```

### Slow Performance

```bash
# Check model is loaded
docker-compose exec ollama ollama list

# Check response time
curl -X POST http://localhost:11434/api/generate -d '{"model":"mistral","prompt":"test","stream":false}' | jq '.eval_duration'

# Optimization: reduce chunk size or increase keep-alive
```

See [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md) for comprehensive troubleshooting.

---

## 📚 Complete Documentation

| Document | Purpose |
|----------|---------|
| **[README.md](README.md)** | This file - overview and quick start |
| **[PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md)** | Deployment, monitoring, tuning, hardening |
| **[ENCRYPTION_GUIDE.md](ENCRYPTION_GUIDE.md)** | Security, compliance (HIPAA/GDPR), best practices |
| **[ENCRYPTION_IMPLEMENTATION_SUMMARY.md](ENCRYPTION_IMPLEMENTATION_SUMMARY.md)** | Encryption quick reference |
| **[CODE_REVIEW.md](CODE_REVIEW.md)** | Code changes, bug fixes, API updates |

---

## 🔐 Security Highlights

✅ **Encryption**
- AES-128 Fernet symmetric encryption
- PBKDF2HMAC key derivation (100k iterations)
- HMAC-based tamper detection
- In-memory decryption only

✅ **Container**
- Non-root user execution
- Dropped Linux capabilities  
- No privilege escalation
- Resource limits enforced

✅ **Compliance**
- HIPAA-aligned design
- GDPR data protection
- Structured audit logging
- Encrypted backups support

---

## 🔧 Common Commands

```bash
# View logs
docker-compose logs -f app
docker-compose logs -f ollama
docker-compose logs -f          # Both

# Check all services
docker-compose ps

# Restart services
docker-compose restart

# Restart specific service
docker-compose restart app

# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes
docker-compose down -v          # WARNING: removes model cache

# Access container shell
docker-compose exec app bash
docker-compose exec ollama bash

# Test API
curl http://localhost:11434/api/tags | jq
```

---

## ✅ Health Check Verification

```bash
# Full health check
docker-compose ps && \
curl -s http://localhost:11434/api/tags | jq '.models | length' && \
echo "✅ All systems operational"

# Individual checks
docker-compose exec ollama curl -f http://localhost:11434/api/tags
docker-compose exec app curl -f http://localhost:8501
```

---

## 📝 License

See [LICENSE](LICENSE) file.

---

## ❓ Need Help?

1. Check [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md#troubleshooting)
2. Review logs: `docker-compose logs`
3. See [ENCRYPTION_GUIDE.md](ENCRYPTION_GUIDE.md) for security issues
4. Open GitHub issue with:
   - Docker versions
   - GPU details
   - Full error message
   - Steps to reproduce

---

**MedVault** - Production-ready medical RAG with enterprise security