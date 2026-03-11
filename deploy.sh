#!/bin/bash

# --- Configuration ---
SERVER_IP="192.168.88.233"
SERVER_USER="uunw"
SERVER_PATH="/home/uunw/isomcom"
ARCHIVE_NAME="isomcom_deploy.tar.gz"

echo "🚀 Starting Deployment Process..."

# 1. Pack the project
echo "📦 Packaging project (excluding unnecessary files)..."
tar -czvf /tmp/$ARCHIVE_NAME \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.ruff_cache' \
    --exclude='uploads/*' \
    .

# 2. Upload to Server
echo "📤 Uploading to $SERVER_IP..."
scp /tmp/$ARCHIVE_NAME $SERVER_USER@$SERVER_IP:$SERVER_PATH/

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to upload file to server."
    exit 1
fi

# 3. Remote Execution
echo "🛠️ Executing remote commands..."
ssh $SERVER_USER@$SERVER_IP << EOF
    cd $SERVER_PATH
    
    echo "📂 Extracting files..."
    tar -xzvf $ARCHIVE_NAME
    
    echo "🐳 Building and Restarting Docker containers..."
    docker compose build
    docker compose down
    docker compose up -d
    
    echo "💾 Running Database Schema Fix and Migration..."
    # รันผ่าน docker exec เพื่อให้มั่นใจว่าใช้ environment เดียวกับตัวแอป
    docker exec isomcom-api uv run python scripts/db_fix.py
    docker exec isomcom-api uv run python scripts/migrate_status.py
    
    echo "🧹 Cleaning up archive..."
    rm $ARCHIVE_NAME
    
    echo "✅ Remote deployment finished!"
EOF

if [ $? -eq 0 ]; then
    echo "✨ Deployment Successful!"
else
    echo "❌ Deployment Failed!"
    exit 1
fi
