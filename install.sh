#!/bin/bash

echo "📦 Installing LLM Memory Bridge..."

# 1. 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 could not be found. Please install Python 3."
    exit 1
fi

# 2. 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# 3. 激活环境并安装依赖
echo "Installing dependencies..."
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖 (统一使用 requirements.txt)
if [ -f "server/requirements.txt" ]; then
    pip install -r server/requirements.txt
else
    echo "⚠️ Warning: server/requirements.txt not found!"
    # Fallback to manual install if file is missing (should not happen in git repo)
    pip install fastapi uvicorn chromadb sentence-transformers mcp[cli] requests google-genai python-dotenv
fi

echo "✅ Installation Complete!"
echo ""
echo "👉 To start the server, run: ./start.sh"
echo "👉 To load the extension, open Chrome -> Extensions -> Load Unpacked -> $(pwd)/extension"