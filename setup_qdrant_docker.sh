#!/bin/bash
# Qdrant Docker Setup Script

echo "🚀 Setting up Qdrant with Docker..."
echo ""

# Check if Qdrant container already exists
if docker ps -a | grep -q qdrant; then
    echo "📦 Qdrant container found"
    
    # Check if it's running
    if docker ps | grep -q qdrant; then
        echo "✅ Qdrant is already running!"
        echo ""
        echo "📍 Qdrant Dashboard: http://localhost:6333/dashboard"
        echo "📍 Qdrant API: http://localhost:6333"
    else
        echo "⚠️  Container exists but not running. Starting it..."
        docker start qdrant
        sleep 2
        echo "✅ Qdrant started!"
        echo ""
        echo "📍 Qdrant Dashboard: http://localhost:6333/dashboard"
        echo "📍 Qdrant API: http://localhost:6333"
    fi
else
    echo "📦 Creating new Qdrant container..."
    
    # Run Qdrant container
    docker run -d \
        --name qdrant \
        -p 6333:6333 \
        -p 6334:6334 \
        -v $(pwd)/qdrant_storage:/qdrant/storage \
        qdrant/qdrant
    
    echo ""
    echo "⏳ Waiting for Qdrant to start..."
    sleep 3
    
    # Check if container is running
    if docker ps | grep -q qdrant; then
        echo "✅ Qdrant is running!"
        echo ""
        echo "📍 Qdrant Dashboard: http://localhost:6333/dashboard"
        echo "📍 Qdrant API: http://localhost:6333"
        echo ""
        echo "💾 Storage: ./qdrant_storage (persistent)"
    else
        echo "❌ Failed to start Qdrant. Check Docker logs:"
        docker logs qdrant
    fi
fi

echo ""
echo "🧪 Testing connection..."
python3 -c "
from qdrant_client import QdrantClient
try:
    client = QdrantClient(host='localhost', port=6333)
    collections = client.get_collections().collections
    print(f'✅ Connection successful!')
    print(f'📦 Collections: {len(collections)}')
    for coll in collections:
        print(f'   - {coll.name}')
except Exception as e:
    print(f'❌ Connection failed: {e}')
"

echo ""
echo "✅ Setup complete!"

