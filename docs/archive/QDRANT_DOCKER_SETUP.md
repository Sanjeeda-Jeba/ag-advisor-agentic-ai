# Qdrant Docker Setup Guide 🐳

## 🚀 Quick Start

### **Option 1: Use the Setup Script (Recommended)**
```bash
./setup_qdrant_docker.sh
```

This script will:
- ✅ Check if Qdrant container exists
- ✅ Start it if it's stopped
- ✅ Create a new one if it doesn't exist
- ✅ Test the connection
- ✅ Show you the dashboard URL

---

### **Option 2: Manual Setup**

#### **Step 1: Start Qdrant Container**
```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

**What this does:**
- `-d`: Run in background (detached mode)
- `--name qdrant`: Name the container "qdrant"
- `-p 6333:6333`: Map port 6333 (HTTP API)
- `-p 6334:6334`: Map port 6334 (gRPC)
- `-v $(pwd)/qdrant_storage:/qdrant/storage`: Persistent storage in `qdrant_storage/` folder

#### **Step 2: Verify It's Running**
```bash
docker ps | grep qdrant
```

You should see:
```
CONTAINER ID   IMAGE           STATUS         PORTS
abc123...      qdrant/qdrant   Up 2 seconds   0.0.0.0:6333->6333/tcp
```

#### **Step 3: Test Connection**
```bash
python -c "from qdrant_client import QdrantClient; client = QdrantClient(host='localhost', port=6333); print('✅ Connected!')"
```

---

## 🌐 Access Qdrant Dashboard

Open your browser:
```
http://localhost:6333/dashboard
```

You can:
- ✅ View collections
- ✅ See stored vectors
- ✅ Search and test queries
- ✅ Monitor performance

---

## 🔧 Common Commands

### **Start Qdrant**
```bash
docker start qdrant
```

### **Stop Qdrant**
```bash
docker stop qdrant
```

### **Restart Qdrant**
```bash
docker restart qdrant
```

### **View Logs**
```bash
docker logs qdrant
```

### **Remove Container (if needed)**
```bash
docker stop qdrant
docker rm qdrant
```

---

## ✅ Verify Your System is Using Docker Qdrant

After starting Qdrant, test:
```bash
python -c "
from src.rag.vector_store import QdrantVectorStore
store = QdrantVectorStore()
if hasattr(store.client, 'host') and store.client.host != ':memory:':
    print(f'✅ Using Docker Qdrant at {store.client.host}:{store.client.port}')
else:
    print('⚠️  Still using in-memory mode')
"
```

---

## 🔍 Troubleshooting

### **Issue: "Connection refused"**
**Solution:**
```bash
# Check if container is running
docker ps | grep qdrant

# If not running, start it
docker start qdrant

# If container doesn't exist, create it
./setup_qdrant_docker.sh
```

### **Issue: "Port already in use"**
**Solution:**
```bash
# Find what's using port 6333
lsof -i :6333

# Stop the process or use a different port
docker run -d --name qdrant -p 6335:6333 qdrant/qdrant
# Then update vector_store.py to use port 6335
```

### **Issue: "Container keeps stopping"**
**Solution:**
```bash
# Check logs
docker logs qdrant

# Common causes:
# - Out of memory
# - Port conflict
# - Permission issues with storage volume
```

---

## 💾 Persistent Storage

Data is stored in:
```
./qdrant_storage/
```

This folder persists even if you stop/remove the container. To keep data:
1. Keep the `qdrant_storage/` folder
2. Use the same volume mount when recreating container

---

## 🚀 Next Steps

After Qdrant is running:

1. **Process PDFs:**
   ```bash
   python src/cdms/document_loader.py
   ```

2. **Test RAG:**
   ```bash
   python src/tools/rag_tool.py
   ```

3. **Check Qdrant:**
   - Open dashboard: http://localhost:6333/dashboard
   - You should see `cdms_documents` collection with vectors

---

## ✅ Success Indicators

After setup, you should see:
- ✅ Container running: `docker ps | grep qdrant`
- ✅ Dashboard accessible: http://localhost:6333/dashboard
- ✅ Python can connect: Test script works
- ✅ Collections visible in dashboard

Your RAG system will now use persistent storage! 🎉

