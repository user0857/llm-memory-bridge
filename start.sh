#!/bin/bash

# 定义日志文件
SERVER_LOG="server.log"
WATCHER_LOG="watcher.log"
SERVER_PID_FILE="server.pid"
WATCHER_PID_FILE="watcher.pid"

echo "🚀 Starting services..."

# 设置 PYTHONPATH，确保 server 目录被包含，以便 import agents 工作正常
export PYTHONPATH=$PYTHONPATH:$(pwd)/server

# 1. 启动 FastAPI Server
echo "-> Starting FastAPI Server..."
nohup venv/bin/uvicorn server.main:app --host 0.0.0.0 --port 8000 > "$SERVER_LOG" 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > "$SERVER_PID_FILE"
echo "   - FastAPI Server started with PID: $SERVER_PID"
echo "   - Log at: $SERVER_LOG"

# 2. 启动文件监听器 (GEMINI.md Syncer)
echo "-> Starting Memory Watcher..."
nohup venv/bin/python tools/watch_memory.py > "$WATCHER_LOG" 2>&1 &
WATCHER_PID=$!
echo $WATCHER_PID > "$WATCHER_PID_FILE"
echo "   - Memory Watcher started with PID: $WATCHER_PID"
echo "   - Log at: $WATCHER_LOG"


echo "✅ All services are up and running."
echo "   - FastAPI Server: http://127.0.0.1:8000"
echo "   - To stop all services, run: ./stop.sh"
