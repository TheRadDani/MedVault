# MedVault Build Guide

Complete step-by-step instructions for building and deploying MedVault in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Windows Setup](#windows-setup)
3. [macOS Setup](#macos-setup)
4. [Linux Setup](#linux-setup)
5. [Building the Application](#building-the-application)
6. [Configuring Encryption](#configuring-encryption)
7. [Starting Services](#starting-services)
8. [Verifying Installation](#verifying-installation)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

1. **Docker** (≥20.10)
   - [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Alternative: [Docker Engine on Linux](https://docs.docker.com/engine/install/)

2. **Docker Compose** (≥1.28)
   - Usually comes with Docker Desktop
   - Verify: `docker-compose --version`

3. **Git**
   - [Download Git](https://git-scm.com/downloads)
   - Verify: `git --version`

4. **System Resources**
   - **Minimum:** 16GB RAM, 30GB disk space
   - **Recommended:** 32GB RAM, 100GB SSD, NVIDIA GPU

### GPU Support (Optional)

For NVIDIA GPU acceleration:

1. **NVIDIA GPU Driver**
   ```bash
   nvidia-smi  # Should show your GPU
   ```

2. **nvidia-docker2** (on Linux)
   ```bash
   distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
     sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update && sudo apt-get install -y nvidia-docker2
   sudo systemctl restart docker
   ```

3. **Docker 24.0+ or Docker Desktop with GPU support**
   - Docker Desktop: Enable GPU in Settings → Resources → GPU
   - Docker on Linux: Already enabled with nvidia-docker2

### Verify Prerequisites

```bash
# Docker installation
docker --version
docker run hello-world

# Docker Compose
docker-compose --version

# GPU support (optional)
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi

# Disk space
df -h /  # Need at least 30GB free

# Memory
free -h  # Need at least 16GB (preferably 32GB)
```

---

## Windows Setup

### Step 1: Install Docker Desktop for Windows

1. Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. Run installer (requires WSL 2 or Hyper-V)
3. Follow installation wizard
4. Restart computer when prompted

### Step 2: Configure Docker Desktop

1. Open Docker Desktop application
2. Go to **Settings** → **Resources**
3. Set **Memory**: 16GB minimum, 32GB recommended
4. Set **CPUs**: 4-8 cores recommended
5. For GPU support: **Settings** → **Resources** → **GPU** → Enable

### Step 3: Enable WSL 2 (if using Windows Home)

```powershell
# Run as Administrator
wsl --install
wsl --set-default-version 2
```

### Step 4: Install Git

1. Download [Git for Windows](https://git-scm.com/downloads)
2. Run installer with default settings
3. Verify in PowerShell:
   ```powershell
   git --version
   ```

### Step 5: Clone Repository

```powershell
cd Documents
git clone https://github.com/yourusername/MedVault.git
cd MedVault
dir  # Should see app/, src/, docker-compose.yml, etc.
```

### Step 6: Configure

```powershell
# Copy configuration template
copy .env.example .env

# Edit .env (optional)
notepad .env
```

### Step 7: Build and Deploy

```powershell
# Build Docker image
docker-compose build app

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### Step 8: Pull Model

```powershell
docker-compose exec ollama ollama pull mistral
```

### Step 9: Access Application

Open browser: `http://localhost:8501`

**Windows-Specific Notes:**
- Use PowerShell or Windows Terminal (not CMD)
- WSL 2 required for Docker Desktop on Home editions
- GPU support requires Windows 11 Professional/Enterprise or NVIDIA drivers

---

## macOS Setup

### Step 1: Install Docker Desktop for Mac

1. Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
   - **Intel:** Any version
   - **Apple Silicon (M1/M2):** Ensure M1 support or later

2. Open DMG file and drag Docker to Applications
3. Launch Docker from Applications
4. Authorize with your password

### Step 2: Configure Docker Desktop

1. Click Docker icon in menu bar → **Preferences**
2. **Resources**:
   - Memory: 16GB min, 32GB recommended
   - CPUs: 4-8 cores
   - Swap: 4GB recommended
   - Disk image size: 120GB+

3. **File Sharing**: Add your home directory (usually automatic)

### Step 3: Install Homebrew (if not installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 4: Install Git

```bash
# Using Homebrew
brew install git

# Verify
git --version
```

### Step 5: Clone Repository

```bash
cd ~/Documents
git clone https://github.com/yourusername/MedVault.git
cd MedVault
ls -la  # Should see app/, src/, docker-compose.yml, etc.
```

### Step 6: Configure

```bash
# Copy configuration template
cp .env.example .env

# Edit .env (optional)
nano .env  # or use your favorite editor
```

### Step 7: Build and Deploy

```bash
# Build Docker image
docker-compose build app

# Start services
docker-compose up -d

# Check status
docker-compose ps

# Watch logs
docker-compose logs -f
```

### Step 8: Pull Model

```bash
# Pull Mistral model (~4GB)
docker-compose exec ollama ollama pull mistral
```

### Step 9: Access Application

```bash
# Open in browser
open http://localhost:8501

# Or manually: http://localhost:8501
```

**macOS-Specific Notes:**
- Apple Silicon (M1/M2) fully supported
- Docker Desktop requires ~5GB disk space
- GPU acceleration via Metal (auto-handled by Docker)
- Performance slower on VMware/Parallels vs native

---

## Linux Setup

### Step 1: Install Docker Engine

**Ubuntu/Debian:**

```bash
# Remove old versions
sudo apt-get remove docker docker-engine docker.io containerd runc

# Add Docker repository
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

**RHEL/CentOS/Fedora:**

```bash
sudo yum install -y docker

# Or for CentOS 8+/RHEL 8+:
sudo dnf install docker-compose-plugin
```

### Step 2: Post-Installation (Run as Non-Root)

```bash
# Create docker group
sudo groupadd docker

# Add your user
sudo usermod -aG docker $USER

# Activate group changes
newgrp docker

# Verify without sudo
docker run hello-world
```

### Step 3: Install Docker Compose (if not included)

```bash
# Check if already installed
docker compose version  # v2.x
docker-compose --version  # v1.x

# If missing, install:
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Step 4: Set Up GPU Support

**NVIDIA GPU:**

```bash
# Install NVIDIA driver
sudo apt-get install -y nvidia-driver-XXX  # XXX = your GPU version

# Verify
nvidia-smi

# Install nvidia-docker2
distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Verify
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
```

### Step 5: Install Git

```bash
# Ubuntu/Debian
sudo apt-get install git

# RHEL/CentOS
sudo yum install git

# Verify
git --version
```

### Step 6: Clone Repository

```bash
# Create workspace directory
mkdir -p ~/projects
cd ~/projects

# Clone repository
git clone https://github.com/yourusername/MedVault.git
cd MedVault

# Verify
ls -la  # Should see app/, src/, docker-compose.yml, etc.
```

### Step 7: Configure

```bash
# Copy configuration template
cp .env.example .env

# Edit .env if needed
nano .env  # or use your editor
```

### Step 8: Build and Deploy

```bash
# Build app image
docker-compose build app

# Start services in background
docker-compose up -d

# Check status
docker-compose ps

# Watch logs (Ctrl+C to stop watching, services keep running)
docker-compose logs -f

# Or watch specific service
docker-compose logs -f app
```

### Step 9: Pull Model

```bash
# Pull Mistral model
docker-compose exec ollama ollama pull mistral

# Wait for completion, then list
docker-compose exec ollama ollama list
```

### Step 10: Access Application

```bash
# Via command line
firefox http://localhost:8501 &  # GNOME/Linux
chromium-browser http://localhost:8501 &  # Chromium

# Or manually: http://localhost:8501 in your browser
```

**Linux-Specific Notes:**
- Best performance on native Linux
- Ensure kernel is updated: `sudo apt-get update && sudo apt-get upgrade`
- SELinux may need policy updates (see troubleshooting)
- Services start automatically after reboot (with `--restart unless-stopped`)

---

## Building the Application

### Understanding the Build Process

```
docker-compose build app
  ↓
Reads Dockerfile
  ↓
Multi-stage build:
  Stage 1 (builder): Installs dependencies (~3GB PyTorch, LangChain, etc)
  Stage 2 (app): Minimal runtime image with installed packages
  ↓
Copies requirements.txt, installs with pip
  ↓
Creates medvault_app:1.0.0 image
```

### Detailed Build Steps

```bash
# Navigate to project
cd MedVault

# Verify Dockerfile exists
ls -la Dockerfile

# Check requirements.txt
head -20 requirements.txt

# Start build (verbose mode)
docker-compose build app --progress=plain

# Progress output:
# #1 [internal] load build definition from Dockerfile
# #2 [auth] library/python:pull token for registry-1.docker.io
# ... downloading base image ...
# #5 [builder 1/5] FROM python:3.11-slim
# #6 [builder 2/5] WORKDIR /build
# ... (many more steps)
# #15 naming to docker.io/library/medvault_app:1.0.0
```

### Build Tips

```bash
# Build without cache (fresh install)
docker-compose build app --no-cache

# Build and keep intermediate images (for debugging)
docker-compose build app --keep-state

# Increase build verbosity
docker-compose build app -v

# View build logs later
docker-compose logs app
```

### Troubleshooting Build Issues

**Issue: "No matching distribution found"**
```
Error: Could not find a version that satisfies the requirement ...
Solution: Check requirements.txt for typos, update package versions
```

**Issue: "pip install timeout"**
```
Solution: Increase network timeout or use different PyPI mirror
docker-compose build app --build-arg PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
```

**Issue: "Out of disk space"**
```
Solution: Clean up Docker images
docker system prune -a
docker image prune -a
# Ensure 50GB+ free space
```

---

## Configuring Encryption

### Enable Encryption (Recommended)

```bash
# Generate encryption key
python -c "from src.encryption import EncryptionManager; print(EncryptionManager.generate_key())"

# Output: gAAAAABl...long-base64-key...

# Copy to .env file
nano .env

# Add these lines:
# ENCRYPTION_KEY=gAAAAABl...long-key-from-above...
# ENCRYPT_DATA_AT_REST=true
```

### Password-Based Encryption

```bash
# Edit .env
nano .env

# Add:
# ENCRYPTION_PASSWORD=my-secure-password
# ENCRYPT_DATA_AT_REST=true
```

### Verify Encryption Setup

```bash
# Run encryption tests
python test_encryption.py

# Expected output:
# ✅ All encryption tests passed!

# Or in container:
docker-compose exec app python test_encryption.py
```

---

## Starting Services

### First-Time Start

```bash
# Start in foreground (watch output)
docker-compose up

# Expected output:
# Creating medvault_ollama ...
# Creating medvault_app ...
# medvault_ollama | Listening on [::]:11434
# medvault_app | You can now view your Streamlit app
```

### Subsequent Starts

```bash
# Start in background
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
docker-compose logs -f ollama
```

### Pull LLM Model

```bash
# After services are running, pull model
docker-compose exec ollama ollama pull mistral

# Monitor progress
# pulling manifest...
# pulling <digest> ... done
# verifying sha256 digest
# writing manifest
# removing any unused layers
# Success!

# Verify
docker-compose exec ollama ollama list
# NAME         ID     QUANTIZATION
# mistral:latest...   Q4_0
```

### Manage Services

```bash
# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart app

# View real-time logs
docker-compose logs -f

# View last 50 lines
docker-compose logs --tail=50
```

---

## Verifying Installation

### Health Checks

```bash
# Container status
docker-compose ps
# Both should show "Up (healthy)"

# Ollama API
curl http://localhost:11434/api/tags | jq '.models'
# Should list: mistral, or other pulled models

# Streamlit app
curl -s http://localhost:8501 | head -20

# Full health check
echo "=== Container Status ===" && \
docker-compose ps && \
echo && \
echo "=== Ollama Models ===" && \
curl -s http://localhost:11434/api/tags | jq '.models[].name' && \
echo && \
echo "=== App Response ===" && \
curl -s http://localhost:8501 | grep -o '<title>.*</title>'
```

### Access Points

```
Web Interface:     http://localhost:8501
Ollama API:        http://localhost:11434
Ollama Models:     http://localhost:11434/api/tags
Vector Store:      ./vector_store/
Data Directory:    ./data/
Logs:              docker-compose logs
```

### Test Data Generation

```bash
# Generate 10 sample records
python -c "
from src.data_generator import generate_dataset
result = generate_dataset(count=10, encrypt=True)
print(f'✅ Generated {result} records')
"
```

---

## Troubleshooting

### General Issues

**Services won't start**

```bash
# Check logs
docker-compose logs

# Common causes:
# - Port already in use: docker ps | grep -E "8501|11434"
# - Insufficient memory: docker stats
# - Docker daemon not running: sudo systemctl start docker

# Solutions:
docker system prune -a  # Clean up
docker-compose up -d    # Try again
```

**Port Conflicts**

```bash
# Find what's using port 8501
lsof -i :8501               # macOS/Linux
netstat -ano | find "8501"  # Windows

# Change port in docker-compose.yml
# ports: "9501:8501"  # Use 9501 instead

# Restart
docker-compose down
docker-compose up -d
```

**GPU Not Working**

```bash
# Check NVIDIA driver
nvidia-smi

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi

# Check Ollama GPU detection
docker logs medvault_ollama | grep -i "cuda\|gpu\|nvidia"

# Install nvidia-docker2 if missing (Linux)
```

**Slow Performance**

```bash
# Check resource usage
docker stats medvault_ollama medvault_app

# Increase allocated resources in Docker Desktop
# Settings → Resources → Memory/CPUs

# Check model in memory
docker-compose exec ollama ollama list

# Restart model loading
docker-compose down
docker-compose up -d
docker-compose exec ollama ollama pull mistral
```

### Platform-Specific Issues

**Windows: "daemon is not running"**
```
Solution: Start Docker Desktop application
          Check Windows → Services for docker service
```

**macOS: "Cannot render color"**  
```
Solution: This is normal, app is running but terminal can't show colors
          Open http://localhost:8501 in browser
```

**Linux: "Permission denied"**
```
Solution: Add user to docker group:
          sudo usermod -aG docker $USER
          Log out and log in again
```

### Performance Tuning

**Slow Queries:**
```bash
# Check inference time
docker-compose exec app python -c "
from src.rag_engine import MedVaultRAG
rag = MedVaultRAG()
import time
start = time.time()
rag.query('test')
print(f'Query took {time.time() - start:.2f}s')
"
```

**High Memory Usage:**
```bash
# Reduce parallelism
# Edit docker-compose.yml: OLLAMA_NUM_PARALLEL=1

# Use smaller model
# docker-compose exec ollama ollama pull phi

# Restart
docker-compose down
docker-compose up -d
```

---

## Next Steps

Once MedVault is running:

1. **Generate Data** - Create synthetic medical records
2. **Configure** - Adjust encryption, models, retrieval parameters
3. **Deploy** - Move to production (see PRODUCTION_GUIDE.md)
4. **Monitor** - Set up logging and monitoring
5. **Secure** - Review security settings in ENCRYPTION_GUIDE.md

---

**Questions?** See [README.md](README.md) or [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md)
