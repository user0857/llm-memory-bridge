#!/bin/bash

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_DIR="$BASE_DIR/server"
LOG_FILE="$SERVER_DIR/server.log"
PID_FILE="$SERVER_DIR/server.pid"

echo "🚀 Starting Gemini Bridge Server..."

# 1. 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "⚠️  Server is already running (PID: $PID)."
        exit 0
    else
        echo "⚠️  Found stale PID file. Cleaning up."
        rm "$PID_FILE"
    fi
fi

# 2. 检查端口 8000 占用
PORT_PID=$(lsof -ti:8000)
if [ ! -z "$PORT_PID" ]; then
    echo "⚠️  Port 8000 is occupied by PID $PORT_PID. Killing it..."
    kill -9 $PORT_PID
    sleep 1
fi

# 3. 启动 Server
cd "$SERVER_DIR" || exit
nohup python main.py > "$LOG_FILE" 2>&1 &
NEW_PID=$!

echo "$NEW_PID" > "$PID_FILE"

# 4. 验证启动
sleep 2
if ps -p $NEW_PID > /dev/null; then
    echo "✅ Server started successfully!"
    echo "   PID: $NEW_PID"
    echo "   Log: $LOG_FILE"
    echo "   API: http://127.0.0.1:8000"
    echo "   Mode: Vector RAG (ChromaDB)"
else
    echo "❌ Server failed to start. Check logs:"
    cat "$LOG_FILE"
fi
