#!/bin/bash

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_DIR="$BASE_DIR/server"
PID_FILE="$SERVER_DIR/server.pid"

echo "🛑 Stopping LLM Memory Bridge..."

# 1. 尝试从 PID 文件关闭
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        kill $PID
        echo "✅ Process $PID stopped."
        rm "$PID_FILE"
    else
        echo "⚠️  Process $PID not found. Removing PID file."
        rm "$PID_FILE"
    fi
else
    echo "ℹ️  No PID file found. Checking port 8000..."
fi

# 2. 兜底：强制清理端口 8000 (防止僵尸进程)
PORT_PID=$(lsof -ti:8000)
if [ ! -z "$PORT_PID" ]; then
    echo "🧹 Cleaning up process on port 8000 (PID: $PORT_PID)..."
    kill -9 $PORT_PID
    echo "✅ Port 8000 freed."
else
    echo "✅ Port 8000 is free."
fi

echo "Done."
