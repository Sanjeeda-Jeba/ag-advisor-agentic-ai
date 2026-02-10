#!/bin/bash
# Quick Qdrant Docker Start Script

echo "🚀 Starting Qdrant with Docker..."
echo ""

# Check if container exists
if docker ps -a | grep -q qdrant; then
    echo "📦 Qdrant container found"
    if docker ps | grep -q qdrant; then
        echo "✅ Qdrant is already running!"
    else
        echo "🔄 Starting existing container..."
        docker start qdrant
        sleep 2
        echo "✅ Qdrant started!"
    fi
else
    echo "📦 Creating new Qdrant container..."
    docker run -d \
        --name qdrant \
        -p 6333:6333 \
        -p 6334:6334 \
        -v "$(pwd)/qdrant_storage:/qdrant/storage" \
        qdrant/qdrant
    
    echo "⏳ Waiting for Qdrant to start..."
    sleep 3
    echo "✅ Qdrant container created and started!"
fi

echo ""
echo "📍 Qdrant Dashboard: http://localhost:6333/dashboard"
echo "📍 Qdrant API: http://localhost:6333"
echo ""
echo "🧪 Testing connection..."
python3 -c "
try:
    from qdrant_client import QdrantClient
    client = QdrantClient(host='localhost', port=6333, timeout=5)
    collections = client.get_collections().collections
    print(f'✅ Connection successful!')
    print(f'📦 Collections: {len(collections)}')
    for coll in collections:
        coll_info = client.get_collection(coll.name)
        print(f'   - {coll.name}: {coll_info.points_count} points')
except Exception as e:
    print(f'❌ Connection failed: {e}')
    print('   Make sure Docker is running and Qdrant container started')
"

echo ""
echo "✅ Done!"

