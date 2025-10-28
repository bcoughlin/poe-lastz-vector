#!/bin/bash
set -e

echo "🔄 Syncing lastz-rag data to Render Disk..."

# Check if /mnt/data is mounted and writable
if [ ! -d "/mnt/data" ]; then
    echo "❌ FATAL ERROR: /mnt/data not found - Render Disk not mounted"
    echo "❌ Please create Render Disk in dashboard first:"
    echo "   1. Go to Render Dashboard -> lastz-bot-v0-8-1"
    echo "   2. Navigate to 'Disks' section"
    echo "   3. Create disk: name=lastz-knowledge-base, mount=/mnt/data, size=1GB"
    echo "   4. Redeploy service"
    exit 1
fi

if [ ! -w "/mnt/data" ]; then
    echo "❌ FATAL ERROR: /mnt/data not writable - permission issue"
    exit 1
fi

echo "✅ /mnt/data is mounted and writable"

DATA_DIR="/mnt/data/lastz-rag"

if [ -d "$DATA_DIR/.git" ]; then
    echo "📦 Data repo exists, pulling latest..."
    cd "$DATA_DIR"
    git pull origin main
    echo "✅ Data updated successfully"
else
    echo "📥 Cloning data repo for first time..."
    cd /mnt/data
    
    # Check if GitHub token is available
    if [ -z "$GITHUB_TOKEN" ]; then
        echo "❌ FATAL ERROR: GITHUB_TOKEN not set and repo is private"
        echo "❌ Add GITHUB_TOKEN environment variable in Render Dashboard"
        echo "❌ Current env vars: $(env | grep -i github || echo 'none')"
        exit 1
    fi
    
    echo "✅ GITHUB_TOKEN found, cloning private repo..."
    # Use token for authentication (token should have 'repo' scope)
    git clone https://${GITHUB_TOKEN}@github.com/bcoughlin/lastz-rag.git
    
    echo "✅ Data cloned successfully"
fi

echo "📊 Data structure:"
ls -la "$DATA_DIR/data/" | head -10
echo "✅ Data sync complete!"
