# MedVault - Production-Ready RAG Pipeline

A scalable, GPU-accelerated Retrieval-Augmented Generation (RAG) pipeline combining Ollama LLMs with a Streamlit interface.

## Features

- **🚀 GPU Acceleration:** Native NVIDIA CUDA support with persistent model caching
- **🔄 Latest APIs:** Ollama v2.6.0 with streaming completions and health checks
- **🏗️ Production-Ready:** Health checks, resource limits, restarts, and structured logging
- **📦 Dockerized:** Multi-stage builds, non-root execution, minimal images
- **⚡ Performance:** Configurable parallelism, VRAM optimization, and request batching
- **🔒 Security:** Read-only filesystems, capability dropping, non-privileged containers

## Quick Start

### Prerequisites
- Docker Engine ≥ 20.10
- Docker Compose ≥ 1.28
- NVIDIA GPU + Container Runtime (recommended)
- 24GB+ RAM, 50GB+ disk space

### 1. Clone & Configure
```bash
cd MedVault
cp .env.production .env
# Edit .env if needed (model names, GPU settings, etc.)
```

### 2. Build & Deploy
```bash
# Build app image
docker-compose build app

# Start services with GPU support
docker-compose up -d

# Verify services running
docker-compose ps
```

### 3. Access the App
- **Streamlit UI:** http://localhost:8501
- **Ollama API:** http://localhost:11434

### 4. Pull Models
```bash
docker-compose exec ollama ollama pull mistral
docker-compose exec ollama ollama pull bge-small
```

## Architecture

```
┌─────────────────────────────────────────┐
│         Streamlit Web Interface         │
│  (http://localhost:8501)                │
├─────────────────────────────────────────┤
│    RAG Application (Python)             │
│  - Query processing                     │
│  - Vector embeddings                    │
│  - Response generation                  │
├─────────────────────────────────────────┤
│    Ollama LLM Inference Engine          │
│  - Mistral, Llama, Neural Chat, etc.   │
│  - GPU-accelerated inference            │
│  - Model caching (persistent)           │
└─────────────────────────────────────────┘
```

## Documentation

- **[PRODUCTION_GUIDE.md](./docs/PRODUCTION_GUIDE.md)** - Full deployment guide, tuning, troubleshooting
- **[docker-compose.yml](./docker-compose.yml)** - Service config (Ollama + App)
- **[Dockerfile](./Dockerfile)** - Multi-stage app build
- **[.env.production](./.env.production)** - Configuration template

## Configuration

### Environment Variables (`.env`)
| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama service endpoint |
| `OLLAMA_NUM_PARALLEL` | `4` | Concurrent request limit |
| `OLLAMA_KEEP_ALIVE` | `5m` | Model keep-alive timeout |
| `DEFAULT_MODEL` | `mistral` | Default LLM |
| `CUDA_VISIBLE_DEVICES` | `0` | GPU indices to use |

### Resource Limits
Adjust in `docker-compose.yml`:
```yaml
ollama:
  cpus: '4.0'           # CPU cores
  mem_limit: 16g        # Memory limit
  # GPU: auto-managed
```

## Performance Tuning

### For 16GB+ GPU
```bash
# In docker-compose.yml
environment:
  OLLAMA_NUM_PARALLEL: 8  # More concurrent requests
  OLLAMA_KEEP_ALIVE: 10m  # Keep model loaded longer
```

### For Limited Resources (8GB GPU)
```bash
environment:
  OLLAMA_NUM_PARALLEL: 2
  DEFAULT_MODEL: phi  # Use smaller model
```

## Common Commands

```bash
# View logs
docker-compose logs -f ollama
docker-compose logs -f app

# Check health
curl http://localhost:11434/api/tags

# Update Ollama version
# Edit docker-compose.yml (image: tag)
docker-compose pull ollama && docker-compose up -d

# Stop services
docker-compose down

# Clean up volumes
docker-compose down -v  # ⚠️ Removes all models
```

## Troubleshooting

**GPU not detected?**
```bash
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
```

**Out of memory?**
```bash
docker stats medvault_ollama  # Check usage
# Reduce OLLAMA_NUM_PARALLEL or use smaller model
```

**See [PRODUCTION_GUIDE.md](./docs/PRODUCTION_GUIDE.md#troubleshooting) for detailed solutions.**

## Security

✅ Non-root container execution  
✅ Read-only filesystems (with /tmp as writable)  
✅ Dropped Linux capabilities  
✅ No privilege escalation  
✅ Pinned image versions  

See **[PRODUCTION_GUIDE.md](./docs/PRODUCTION_GUIDE.md#security-hardening-optional)** for hardening options.

## API Reference

### Ollama Endpoints
All requests use internal service address: `http://ollama:11434`

**List models:**
```bash
curl http://localhost:11434/api/tags
```

**Generate completion:**
```bash
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral", "prompt": "What is RAG?"}'
```

Full API docs: https://github.com/ollama/ollama/blob/main/docs/api.md

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|------------|
| RAM | 16GB | 32GB+ |
| GPU VRAM | 4GB | 16GB+ |
| Disk | 30GB | 100GB SSD |
| Docker | 20.10 | 24.0+ |
| Compose | 1.28 | 2.20+ |

## License

See [LICENSE](./LICENSE) file.

---

**Need help?** Check logs:
```bash
docker-compose logs --tail=50
```