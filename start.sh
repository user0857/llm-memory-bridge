#!/bin/bash

# 获取脚本所在目录，确保在任何地方执行都能找到路径
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_DIR="$BASE_DIR/server"
LOG_FILE="$SERVER_DIR/server.log"
PID_FILE="$SERVER_DIR/server.pid"
VENV_PYTHON="$BASE_DIR/venv/bin/python"

echo "🚀 Starting LLM Memory Bridge..."

# 1. 检查虚拟环境
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Virtual environment not found. Please run ./install.sh first."
    exit 1
fi

# 2. 检查是否已经在运行 (通过 PID 文件)
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

# 3. 检查端口 8000 是否被占用 (防止冲突)
PORT_PID=$(lsof -ti:8000)
if [ ! -z "$PORT_PID" ]; then
    echo "⚠️  Port 8000 is occupied by PID $PORT_PID. Killing it..."
    kill -9 $PORT_PID
    sleep 1
fi

# 4. 启动 Server (后台运行)
echo "   Executing: $VENV_PYTHON server/main.py"
cd "$BASE_DIR" # 确保在根目录运行，这样 imports 正常
nohup "$VENV_PYTHON" server/main.py > "$LOG_FILE" 2>&1 &
NEW_PID=$!

echo "$NEW_PID" > "$PID_FILE"

# 5. 验证是否启动成功
sleep 2
if ps -p $NEW_PID > /dev/null; then
    echo "✅ Server started successfully!"
    echo "   PID: $NEW_PID"
    echo "   Log: $LOG_FILE"
    echo "   API: http://127.0.0.1:8000"
    echo "   Docs: http://127.0.0.1:8000/docs"
else
    echo "❌ Server failed to start. Check logs:"
    cat "$LOG_FILE"
fi
