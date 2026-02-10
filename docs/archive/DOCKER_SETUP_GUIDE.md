# Docker Installation Guide for macOS

## 🐳 Installing Docker on macOS (Your System)

You're on **macOS 25.0.0**, so here are the installation options:

---

## ✅ Option 1: Docker Desktop (Recommended - Easy GUI)

### Step 1: Download Docker Desktop
1. Go to: https://www.docker.com/products/docker-desktop
2. Click **"Download for Mac"**
3. Choose your Mac type:
   - **Apple Silicon (M1/M2/M3)**: Download "Mac with Apple chip"
   - **Intel Mac**: Download "Mac with Intel chip"

### Step 2: Install Docker Desktop
```bash
# 1. Open the downloaded .dmg file (Docker.dmg)
# 2. Drag Docker icon to Applications folder
# 3. Open Docker from Applications folder
# 4. Follow the setup wizard
# 5. Docker will ask for system permissions - grant them
```

### Step 3: Verify Installation
```bash
# Open Terminal and run:
docker --version
# Should output: Docker version 24.x.x or similar

docker ps
# Should output: CONTAINER ID   IMAGE   ... (empty list is fine)
```

### Step 4: Run Qdrant Container
```bash
# Pull Qdrant image
docker pull qdrant/qdrant

# Run Qdrant container
docker run -d -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/data/qdrant_storage:/qdrant/storage \
    --name qdrant_demo \
    qdrant/qdrant

# Verify it's running
docker ps
# Should show qdrant_demo container running

# Test Qdrant is accessible
curl http://localhost:6333
# Should return: {"title":"qdrant - vector search engine",...}
```

---

## ⚡ Option 2: Homebrew (Command Line - Faster)

If you have Homebrew installed:

```bash
# Install Docker
brew install --cask docker

# Open Docker Desktop
open /Applications/Docker.app

# Wait for Docker to start (watch for whale icon in menu bar)

# Verify
docker --version
```

---

## 🔧 Option 3: Colima (Lightweight, No GUI)

If you want Docker without Docker Desktop (lighter weight):

```bash
# Install Colima via Homebrew
brew install colima docker

# Start Colima
colima start

# Verify
docker --version
docker ps
```

---

## 🎯 After Docker is Running

### Start Qdrant for Your Project
```bash
# Navigate to your project
cd /Users/sanjeedajeba/agentic_ai_project

# Create data directory for Qdrant persistence
mkdir -p data/qdrant_storage

# Run Qdrant container
docker run -d \
    -p 6333:6333 \
    -p 6334:6334 \
    -v $(pwd)/data/qdrant_storage:/qdrant/storage \
    --name qdrant_demo \
    qdrant/qdrant

# Verify Qdrant is running
curl http://localhost:6333
# Expected output: {"title":"qdrant - vector search engine",...}

# Or open in browser: http://localhost:6333/dashboard
```

---

## 🔍 Useful Docker Commands for Qdrant

### Check if Qdrant is Running
```bash
docker ps
# Look for qdrant_demo in the list
```

### Stop Qdrant
```bash
docker stop qdrant_demo
```

### Start Qdrant (if stopped)
```bash
docker start qdrant_demo
```

### View Qdrant Logs
```bash
docker logs qdrant_demo
```

### Remove Qdrant Container (to start fresh)
```bash
docker stop qdrant_demo
docker rm qdrant_demo
# Then run the docker run command again
```

### Access Qdrant Dashboard
```bash
# Open in browser:
# http://localhost:6333/dashboard
```

---

## ❌ Alternative: No Docker? Use In-Memory Mode

If you can't or don't want to install Docker, you can run Qdrant in-memory mode:

### Modify the Code
In your RAG implementation, when initializing Qdrant:

```python
# Instead of:
from qdrant_client import QdrantClient
client = QdrantClient(host="localhost", port=6333)

# Use in-memory mode:
from qdrant_client import QdrantClient
client = QdrantClient(":memory:")  # No Docker needed!
```

### Pros & Cons of In-Memory Mode

**Pros:**
- ✅ No Docker installation needed
- ✅ Faster startup
- ✅ Simpler for quick demos

**Cons:**
- ❌ Data lost when app stops (no persistence)
- ❌ Limited to available RAM
- ❌ Have to re-index PDFs each time

**Recommendation:** Use in-memory mode for initial testing, then move to Docker for persistence.

---

## 🐛 Troubleshooting

### Issue: "docker: command not found"
**Solution:** Docker is not in your PATH. Try:
```bash
# Restart terminal
# Or add to PATH:
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
```

### Issue: "Cannot connect to the Docker daemon"
**Solution:** Docker Desktop is not running. Open Docker Desktop app from Applications.

### Issue: "Port 6333 is already in use"
**Solution:** Another service is using that port. Either:
```bash
# Option 1: Find and stop the process
lsof -i :6333
kill -9 <PID>

# Option 2: Use different port
docker run -d -p 6335:6333 --name qdrant_demo qdrant/qdrant
# Then update your code to use port 6335
```

### Issue: "Docker Desktop requires macOS 10.15 or later"
**Solution:** You're on macOS 25.0.0, so this shouldn't be an issue. But if you get version errors:
- Update macOS to latest version
- Or use Colima (Option 3) instead

---

## 📊 System Requirements

### Docker Desktop:
- **RAM:** 4GB minimum, 8GB+ recommended
- **Disk:** 4GB minimum for Docker Desktop + images
- **macOS:** 10.15 (Catalina) or later ✅ (You have 25.0.0)

### Qdrant Container:
- **RAM:** ~200MB per container
- **Disk:** ~100MB for image, varies for data

---

## ✅ Quick Test After Installation

```bash
# 1. Check Docker is working
docker run hello-world

# 2. Start Qdrant
docker run -d -p 6333:6333 --name qdrant_test qdrant/qdrant

# 3. Test Qdrant
curl http://localhost:6333

# 4. Clean up test
docker stop qdrant_test
docker rm qdrant_test
```

---

## 🎬 Ready for Your Project

Once Docker is installed and Qdrant is running, you can proceed with:

1. ✅ Docker installed and running
2. ✅ Qdrant container running on port 6333
3. ✅ Can access http://localhost:6333
4. 🚀 Ready to implement RAG system!

---

## 💡 Pro Tips

1. **Docker Desktop Memory:** 
   - Go to Docker Desktop → Settings → Resources
   - Allocate at least 4GB RAM for smooth operation

2. **Auto-start Qdrant:**
   ```bash
   # Add --restart unless-stopped to docker run command
   docker run -d --restart unless-stopped \
       -p 6333:6333 \
       -v $(pwd)/data/qdrant_storage:/qdrant/storage \
       --name qdrant_demo \
       qdrant/qdrant
   ```

3. **Backup Qdrant Data:**
   ```bash
   # Your data is in: data/qdrant_storage/
   # Just backup that folder
   cp -r data/qdrant_storage data/qdrant_backup
   ```

---

**Need help? Let me know which option you chose and if you encounter any issues!**

