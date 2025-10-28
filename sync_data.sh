#!/bin/bash
set -e

echo "🔄 Syncing lastz-rag data to Render Disk..."

DATA_DIR="/mnt/data/lastz-rag"

if [ -d "$DATA_DIR/.git" ]; then
    echo "📦 Data repo exists, pulling latest..."
    cd "$DATA_DIR"
    git pull origin main
    echo "✅ Data updated successfully"
else
    echo "📥 Cloning data repo for first time..."
    mkdir -p /mnt/data
    cd /mnt/data
    git clone https://github.com/bcoughlin/lastz-rag.git
    echo "✅ Data cloned successfully"
fi

echo "📊 Data structure:"
ls -la "$DATA_DIR/data/" | head -10
echo "✅ Data sync complete!"
