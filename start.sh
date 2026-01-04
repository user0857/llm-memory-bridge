#!/bin/bash

# 获取脚本所在目录
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./install.sh first."
    exit 1
fi

source venv/bin/activate

# 启动 Server
echo "🚀 Starting Gemini Bridge Server..."
cd server
# 使用 nohup 后台运行，日志输出到 server.log
nohup python main.py > server.log 2>&1 &
SERVER_PID=$!
echo "✅ Server running with PID: $SERVER_PID"
echo "   API: http://127.0.0.1:8000"
echo "   Logs: $BASE_DIR/server/server.log"

echo ""
echo "💡 Tips:"
echo "   - To stop the server, run: kill $SERVER_PID"
echo "   - To use CLI: source venv/bin/activate && python cli/client.py"
