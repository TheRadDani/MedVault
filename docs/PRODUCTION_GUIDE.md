# MedVault RAG Pipeline - Production Deployment Guide

## Overview
This docker-compose setup is production-ready with:
- ✅ GPU acceleration (NVIDIA CUDA)
- ✅ Latest Ollama API (v2.6.0)
- ✅ Health checks & automatic restarts
- ✅ Resource limits (CPU/Memory)
- ✅ Security hardening
- ✅ Persistent model storage
- ✅ Structured logging
- ✅ Non-root execution

## Prerequisites

### System Requirements
- **Docker Engine >= 20.10** (for GPU support)
- **Docker Compose >= 1.28** (for `gpus` syntax)
- **NVIDIA GPU** (optional but recommended for performance)
- **NVIDIA Container Runtime** (`nvidia-docker` or integrated)
- **Minimum Memory:** 24GB RAM (16GB Ollama + 8GB App)
- **Available Disk:** 50GB+ for models (depends on which LLM you use)

### Check Docker GPU Support
```bash
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
```

## Quick Start

### 1. Setup Environment
```bash
cd MedVault
cp .env.production .env  # Customize if needed
```

### 2. Build the App Image
```bash
docker-compose build app
```

### 3. Start the Pipeline (with GPU)
```bash
docker-compose up -d
```

### 4. Verify Services
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f ollama
docker-compose logs -f app

# Test Ollama API
curl http://localhost:11434/api/tags

# Access Streamlit UI
# Open http://localhost:8501 in your browser
```

### 5. Pull/Load Models (if not auto-loading)
```bash
docker-compose exec ollama ollama pull mistral
docker-compose exec ollama ollama pull bge-small
```

## Performance Tuning

### GPU Optimization
```bash
# Check GPU memory usage
docker-compose exec ollama nvidia-smi

# Adjust in docker-compose.yml:
# - OLLAMA_NUM_GPU: increase to use more VRAM
# - OLLAMA_NUM_PARALLEL: increase for concurrent requests
# - cpus: '4.0' → increase CPU allocation if bottlenecked
```

### Memory Settings
```yaml
# For 16GB GPU + 32GB RAM:
ollama:
  cpus: '6.0'
  mem_limit: 20g
  environment:
    OLLAMA_NUM_PARALLEL: 8
```

### Model Selection Impact
- **Mistral 7B:** ~4GB VRAM (default for RAG)
- **Llama 2 13B:** ~8GB VRAM
- **Neural Chat:** ~5GB VRAM
- **Phi 2:** ~2GB VRAM (lightweight)

## Production Checklist

- [ ] **Image Versions:** Pin all image tags (no `:latest`)
- [ ] **Environment:** Create `.env` with production settings
- [ ] **Volumes:** Ensure persistent storage on reliable disk/NAS
- [ ] **Backups:** Schedule backup of `ollama_data` volume
- [ ] **Networking:** Use firewall rules (don't expose ports to public)
- [ ] **Monitoring:** Set up container monitoring (Prometheus/Grafana optional)
- [ ] **Restarts:** Configure `restart: unless-stopped` (done)
- [ ] **Logging:** Monitor logs with `docker-compose logs`
- [ ] **Health:** Verify health checks pass (`docker-compose ps`)

## Troubleshooting

### GPU Not Being Used
```bash
# Verify NVIDIA runtime
docker run --rm --gpus all ubuntu nvidia-smi

# Check docker-compose.yml gpus section
# Ensure docker daemon supports nvidia runtime:
docker info | grep nvidia
```

### Out of Memory Errors
```bash
# Check current usage
docker stats medvault_ollama medvault_app

# Solutions:
# 1. Increase host memory
# 2. Reduce OLLAMA_NUM_PARALLEL
# 3. Use a smaller model
# 4. Decrease mem_limit to allow proper OOM kills
```

### Ollama API Not Responding
```bash
# Check healthcheck
docker-compose ps
docker-compose logs ollama | tail -50

# Manually test
curl -v http://localhost:11434/api/tags
docker-compose exec app curl http://ollama:11434/api/tags
```

### Slow Response Times
```bash
# Check GPU saturation
docker stats  # Look at % of container memory/CPU

# Solutions:
# 1. Reduce concurrent requests (OLLAMA_NUM_PARALLEL)
# 2. Use smaller model
# 3. Increase GPU count if available
# 4. Add load balancer (for multi-instance)
```

## API Reference

### Ollama HTTP Endpoints (v2.6.0)
All requests are from container internal address: `http://ollama:11434`

**List Available Models**
```bash
curl http://ollama:11434/api/tags
```

**Generate Completion**
```bash
curl -X POST http://ollama:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "prompt": "Your question here",
    "stream": false
  }'
```

**Streaming Response**
```python
import requests
response = requests.post(
    'http://ollama:11434/api/generate',
    json={'model': 'mistral', 'prompt': 'hello', 'stream': True},
    stream=True
)
for line in response.iter_lines():
    print(line)
```

## Updates & Maintenance

### Update Ollama Version
```bash
# Edit docker-compose.yml
# Change: image: ollama/ollama:2.6.0
# To: image: ollama/ollama:2.7.0 (when available)

docker-compose pull ollama
docker-compose up -d ollama
```

### Backup Models
```bash
# Backup volume
docker run --rm \
  -v medvault_ollama_data:/data \
  -v /backup:/backup \
  alpine tar czf /backup/ollama-backup.tar.gz -C /data .
```

### Clean Up (Prune)
```bash
# Remove stopped containers
docker-compose down

# Prune unused images/volumes (be careful!)
docker system prune -a --volumes
```

## Security Hardening (Optional)

For even stricter production:
1. **Network Isolation:** Use overlay networks only
2. **Read-Only Root:** All services use `read_only: true`
3. **Capability Dropping:** `cap_drop: [ALL]` with minimal `cap_add`
4. **Resource Quotas:** Set hard limits on CPU/memory
5. **Image Scanning:** Use Trivy or similar for vulnerability checks
6. **Secrets Management:** Use Docker Secrets or external key vaults

## Monitoring & Logging

### View Real-Time Logs
```bash
docker-compose logs -f --tail=100
```

### Export Logs
```bash
docker-compose logs > deployment.log
```

### Container Stats
```bash
docker stats --no-stream medvault_ollama medvault_app
```

---

**Questions?** Review logs and health checks first:
```bash
docker-compose ps  # Status
docker-compose logs  # Full logs
```
