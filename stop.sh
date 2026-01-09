#!/bin/bash

SERVER_PID_FILE="server.pid"
WATCHER_PID_FILE="watcher.pid"

echo "🛑 Stopping services..."

# 停止 FastAPI Server
if [ -f "$SERVER_PID_FILE" ]; then
    PID=$(cat "$SERVER_PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "   - Killing FastAPI Server (PID: $PID)"
        kill $PID
        rm "$SERVER_PID_FILE"
    else
        echo "   - FastAPI Server already stopped."
        rm "$SERVER_PID_FILE"
    fi
else
    echo "   - FastAPI Server PID file not found."
fi

# 停止 Memory Watcher
if [ -f "$WATCHER_PID_FILE" ]; then
    PID=$(cat "$WATCHER_PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "   - Killing Memory Watcher (PID: $PID)"
        kill $PID
        rm "$WATCHER_PID_FILE"
    else
        echo "   - Memory Watcher already stopped."
        rm "$WATCHER_PID_FILE"
    fi
else
    echo "   - Memory Watcher PID file not found."
fi

echo "✅ All services stopped."