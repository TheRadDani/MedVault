# MedVault Quick Start (5 Minutes)

Get MedVault running in 5 minutes. For detailed instructions, see [BUILD_GUIDE.md](BUILD_GUIDE.md).

## Prerequisites

- ✅ Docker installed (`docker --version`)
- ✅ Docker Compose installed (`docker-compose --version`)
- ✅ 16GB+ RAM
- ✅ 30GB+ free disk space

## 1. Clone & Setup (1 minute)

```bash
# Clone repository
git clone https://github.com/yourusername/MedVault.git
cd MedVault

# Copy configuration
cp .env.example .env
```

## 2. Build (2 minutes)

```bash
# Build Docker image
docker-compose build app

# You'll see:
# #1 [internal] load build definition
# ... downloading dependencies ...
# Successfully built medvault_app:1.0.0
```

## 3. Start Services (1 minute)

```bash
# Start both Ollama and Streamlit
docker-compose up -d

# Check they're running
docker-compose ps

# Expected output:
# medvault_app      up (healthy)
# medvault_ollama   up (healthy)
```

## 4. Download Model (30 seconds)

```bash
# Pull Mistral model (~4GB)
docker-compose exec ollama ollama pull mistral

# Wait for:
# pulling manifest... done
```

## 5. Open Application (instant)

```bash
# Open browser
http://localhost:8501
```

---

## Common Tasks

### Query Documents

1. Go to **Data Management** tab
2. Select "Generate Sample Data"
3. Click "Generate & Ingest"
4. Go to **Query Documents** tab
5. Enter your question
6. Click "Search"

### Check System Health

```bash
# View container status
docker-compose ps

# Check Ollama
curl http://localhost:11434/api/tags

# View logs
docker-compose logs -f app
docker-compose logs -f ollama
```

### Stop/Restart Services

```bash
# Stop services
docker-compose stop

# Restart services
docker-compose restart

# Stop and remove (keeps data)
docker-compose down

# Stop and remove everything (data too)
docker-compose down -v
```

---

## Enable Encryption (Optional)

```bash
# Generate key
python -c "from src.encryption import EncryptionManager; print(EncryptionManager.generate_key())"

# Add to .env
# ENCRYPTION_KEY=gAAAAABl...
# ENCRYPT_DATA_AT_REST=true

# Restart app
docker-compose restart app
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8501 in use | Change port in docker-compose.yml, restart |
| GPU not detected | Install nvidia-docker2, check nvidia-smi |
| Out of memory | Reduce OLLAMA_NUM_PARALLEL, restart services |
| Slow queries | Check `docker stats`, increase resources |

---

## What's Next?

- **[README.md](README.md)** - Full overview and features
- **[BUILD_GUIDE.md](BUILD_GUIDE.md)** - Detailed build instructions  
- **[PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md)** - Production deployment
- **[ENCRYPTION_GUIDE.md](ENCRYPTION_GUIDE.md)** - Security setup

---

**✅ You're ready!** Start using MedVault at http://localhost:8501
