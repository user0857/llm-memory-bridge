#!/bin/bash

echo "📦 Installing Gemini Memory Bridge..."

# 1. 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 could not be found. Please install Python 3."
    exit 1
fi

# 2. 创建虚拟环境 (推荐)
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# 3. 激活环境并安装依赖
echo "Installing dependencies..."
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装 Server 依赖
pip install fastapi uvicorn pydantic chromadb sentence-transformers

# 安装 CLI 依赖
pip install google-generativeai requests rich

echo "✅ Installation Complete!"
echo ""
echo "👉 To start the server, run: ./start.sh"
echo "👉 To load the extension, open Chrome -> Extensions -> Load Unpacked -> $(pwd)/extension"
