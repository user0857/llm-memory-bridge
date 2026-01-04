# Gemini Memory Bridge 🧠

**Gemini Memory Bridge** 是一个开源工具，旨在打破 Gemini 网页端与本地开发环境（CLI）之间的记忆隔阂。

它允许你：
1.  **Web 记忆同步**：你在 `gemini.google.com` 的对话会自动沉淀到本地知识库。
2.  **RAG 增强**：当你在网页或 CLI 提问时，系统会自动检索相关的历史记忆并注入上下文，让 AI 永远记得你的偏好、代号和项目细节。
3.  **完全隐私**：所有记忆数据（Vector DB）仅存储在你的本地电脑上，不经过任何第三方云服务。

## 🚀 快速开始

### 1. 安装
```bash
# 1. 克隆项目
git clone https://github.com/yourname/gemini-memory-bridge.git
cd gemini-memory-bridge

# 2. 运行安装脚本 (Mac/Linux)
chmod +x install.sh start.sh
./install.sh
```

### 2. 启动服务
```bash
./start.sh
```
首次启动时会自动下载 AI 模型（约 400MB），请耐心等待几分钟。

### 3. 安装 Chrome 插件
1.  打开 Chrome 浏览器，访问 `chrome://extensions/`。
2.  开启右上角的 **Developer mode (开发者模式)**。
3.  点击 **Load unpacked**，选择本项目下的 `extension/` 文件夹。
4.  刷新 `gemini.google.com`，看到右下角出现灰色的 "M" 图标即成功。

### 4. 使用 CLI
```bash
# 激活环境
source venv/bin/activate

# 运行 CLI
export GEMINI_API_KEY="你的_API_KEY"
python cli/client.py
```

## 🛠️ 功能特性
*   **Vector RAG**: 使用 `paraphrase-multilingual-MiniLM-L12-v2` 模型进行多语言语义检索。
*   **Chrome Extension**: 智能防抖监听，支持输入法 (IME) 冲突检测，自动抓取 Markdown 格式回复。
*   **Privacy First**: 基于 ChromaDB 的本地向量存储。

## 📝 目录结构
*   `server/`: FastAPI + ChromaDB 后端服务。
*   `extension/`: Chrome 浏览器插件源码。
*   `cli/`: 终端聊天客户端。

## ⚠️ 注意事项
*   Server 默认运行在 `8000` 端口。
*   插件仅在 `gemini.google.com` 生效。

License: MIT
