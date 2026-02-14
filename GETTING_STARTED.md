# Getting Started with MedVault

Choose your starting point:

## ⚡ I'm Impatient (5 Min)
Go to [QUICK_START.md](QUICK_START.md) - Clone, build, run, done!

## 📖 I Want Full Details (30 Min)
Go to [BUILD_GUIDE.md](BUILD_GUIDE.md) - Platform-specific setup with troubleshooting

## 🏢 I'm Deploying to Production
Go to [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md) - Complete deployment reference

## 🔐 I Need Security/Encryption
Go to [ENCRYPTION_GUIDE.md](ENCRYPTION_GUIDE.md) - HIPAA/GDPR-aligned security

---

## Step-by-Step by Role

### 👨‍💻 Developer - Local Development

1. **Quick Start:**
   ```bash
   git clone https://github.com/yourusername/MedVault.git
   cd MedVault
   docker-compose up -d
   docker-compose exec ollama ollama pull mistral
   # Open http://localhost:8501
   ```

2. **Read:** [BUILD_GUIDE.md](BUILD_GUIDE.md) (your OS section)

3. **Customize:** Edit `.env` for your preferences

4. **Code:** See [src/](src/) directory structure

### 🔐 Security Admin - Encryption Setup

1. **Quick Start:** [QUICK_START.md](QUICK_START.md)

2. **Generate Key:**
   ```bash
   python -c "from src.encryption import EncryptionManager; print(EncryptionManager.generate_key())"
   ```

3. **Configure:** Add to `.env`:
   ```
   ENCRYPTION_KEY=gAAAAABl...
   ENCRYPT_DATA_AT_REST=true
   ```

4. **Verify:**
   ```bash
   python test_encryption.py
   ```

5. **Read:** [ENCRYPTION_GUIDE.md](ENCRYPTION_GUIDE.md) (compliance section)

### 🚀 DevOps/Platform Engineer - Production Deployment

1. **Infrastructure:**
   - Minimum 32GB RAM, 100GB SSD
   - NVIDIA GPU recommended (RTX 4090+ optimal)
   - Docker 24.0+ with GPU support

2. **Setup:** [BUILD_GUIDE.md](BUILD_GUIDE.md) for your OS

3. **Production Hardening:** [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md)

4. **Monitoring:** Set up health checks and logging

5. **Scaling:** See load balancing section in PRODUCTION_GUIDE.md

### 👨‍⚕️ Domain Expert - Medical Data

1. **Quick Start:** [QUICK_START.md](QUICK_START.md)

2. **Generate Data:**
   - Use Data Management tab in UI
   - Or: `python -c "from src.data_generator import generate_dataset; generate_dataset(count=100)"`

3. **Encryption Setup:** [ENCRYPTION_GUIDE.md](ENCRYPTION_GUIDE.md)
   - HIPAA section
   - Data retention policy

4. **Query:** Use natural language in Query Documents tab

---

## Common Scenarios

### "I want to run this on my laptop - Windows"
→ [BUILD_GUIDE.md - Windows Section](BUILD_GUIDE.md#windows-setup)

### "I want to run this on my laptop - Mac"  
→ [BUILD_GUIDE.md - macOS Section](BUILD_GUIDE.md#macos-setup)

### "I want to run this on a Linux server"
→ [BUILD_GUIDE.md - Linux Section](BUILD_GUIDE.md#linux-setup)

### "I have an NVIDIA GPU - how do I use it?"
→ [BUILD_GUIDE.md - GPU Support Section](BUILD_GUIDE.md#step-4-set-up-gpu-support)

### "I need encryption for HIPAA compliance"
→ [ENCRYPTION_GUIDE.md - Compliance Section](ENCRYPTION_GUIDE.md#compliance)

### "My app is slow - how do I tune it?"
→ [BUILD_GUIDE.md - Performance Tuning](BUILD_GUIDE.md#performance-tuning) or [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md#performance-optimization)

### "Docker containers won't start"
→ [BUILD_GUIDE.md - Troubleshooting Section](BUILD_GUIDE.md#troubleshooting)

### "I have an error - where do I find help?"
→ Check logs: `docker-compose logs -f`, then [troubleshooting guides](BUILD_GUIDE.md#troubleshooting)

---

## File Overview

| File | Purpose | Read Time |
|------|---------|-----------|
| [README.md](README.md) | Overview, features, architecture | 5 min |
| [QUICK_START.md](QUICK_START.md) | Get running in 5 minutes | 5 min |
| [BUILD_GUIDE.md](BUILD_GUIDE.md) | Complete build guide for all platforms | 30 min |
| [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md) | Production deployment, tuning, monitoring | 45 min |
| [ENCRYPTION_GUIDE.md](ENCRYPTION_GUIDE.md) | Encryption, security, compliance | 30 min |
| [CODE_REVIEW.md](CODE_REVIEW.md) | Technical code changes, API updates | 15 min |

---

## Prerequisites Checklist

- [ ] Docker installed (`docker --version`)
- [ ] Docker Compose installed (`docker-compose --version`)
- [ ] Git installed (`git --version`)
- [ ] 16GB+ RAM available
- [ ] 30GB+ disk space available
- [ ] (Optional) NVIDIA GPU with drivers

**Don't have these?** See [BUILD_GUIDE.md - Prerequisites](BUILD_GUIDE.md#prerequisites)

---

## Next Steps After Installation

1. **Verify Installation:** `docker-compose ps` (both should be healthy)
2. **Generate Sample Data:** Use Data Management tab or CLI
3. **Try Querying:** Query Documents tab with a question
4. **Configure Encryption:** Follow [ENCRYPTION_GUIDE.md](ENCRYPTION_GUIDE.md)
5. **Read Full Docs:** [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md) for deployment

---

## Quick Help Commands

```bash
# Check everything is running
docker-compose ps

# View logs
docker-compose logs -f app

# Stop everything
docker-compose stop

# Restart everything
docker-compose restart

# Full cleanup (WARNING: removes data)
docker-compose down -v

# Test encryption
python test_encryption.py

# Access logs directory
ls -la logs/

# Check GPU (if available)
nvidia-smi
```

---

## Still Have Questions?

1. **General Setup:** See [BUILD_GUIDE.md](BUILD_GUIDE.md)
2. **Production Deployment:** See [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md)
3. **Security/Encryption:** See [ENCRYPTION_GUIDE.md](ENCRYPTION_GUIDE.md)
4. **Code Details:** See [CODE_REVIEW.md](CODE_REVIEW.md)
5. **Quick Reference:** See [QUICK_START.md](QUICK_START.md)

---

**Choose your path above to get started! 🚀**
