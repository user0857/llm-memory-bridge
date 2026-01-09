# LLM Memory Bridge (记忆神经中枢)

**LLM Memory Bridge** 是一个打通浏览器 AI 对话与本地长期记忆库的“神经桥梁”。它让 Google Gemini、Claude 等 AI 拥有跨会话的长期记忆能力，并支持通过 MCP (Model Context Protocol) 供 Claude Desktop、Cursor 等 Agent 调用。

本项目采用 **Google Gemini API** 作为 "Gatekeeper"（守门人），负责对进入记忆库的信息进行智能清洗、摘要和标签化，确保记忆的高质量。

![架构图](./architecture.svg)

## ✨ 核心特性

### 🛡️ Gatekeeper Agent (云端守门人)
- **智能清洗**: 由 Google Gemini Pro/Flash 驱动，自动识别输入意图（保存/更新/忽略）。
- **隐私保护**: 自动剔除无关闲聊，提取核心事实。
- **自动摘要**: 为网页内容或长对话生成精炼摘要并自动打标签。
- **来源追踪**: 精确记录记忆来源，支持 `'mcp'` (CLI/Cursor), `'web_extension'` (浏览器), `'file_watcher'` (本地文件)。

### 👓 浏览器感知 (Extension)
- **全能悬浮球 (FAB)**: 
    - 🔴 **红色**: 离线/错误
    - 🔵 **蓝色**: Gatekeeper 处理中 (清洗/保存)
    - 🟢 **绿色**: 就绪/成功
- **Web Clipper**: 自动识别网页内容，一键清洗并存入向量库。
- **现代化 Popup 面板**:
    - **极简设计**: 适配现代审美，提供清晰的状态指示。
    - **快捷搜索**: 支持对历史记忆进行关键词检索。
    - **一键复制**: 快捷按钮将记忆内容复制到剪贴板，带 ✅ 反馈。
    - **智能删除**: 悬浮显示的清理按钮，轻松管理存储。
- **RAG 注入**: 实时检索 ChromaDB 中的相关历史，并在 Gemini 网页版对话框中提供上下文注入。

### 🔌 MCP 协议支持
- 完美兼容 **Claude Desktop**, **Cursor** 等支持 MCP 的客户端。
- **工具集**:
    - `search_memory`: 语义检索。
    - `save_memory`: 智能存储（经 Gatekeeper 处理）。
    - `update_memory`: 结合上下文更新旧记忆。
    - `delete_memory`: 遗忘与清理。

### 📂 本地文件同步 (File Watcher)
- 监听指定目录（如 `.gemini/GEMINI.md`），将本地笔记变动实时同步至向量数据库。

## 🛠 技术栈
- **Gatekeeper Engine**: Google Gemini API (`google-genai`).
- **Backend**: FastAPI, ChromaDB (向量库), Sentence-Transformers (嵌入模型).
- **Frontend**: Chrome Extension (Vanilla JS, Content-Script-Driven).
- **Protocol**: Model Context Protocol (MCP).

## 📂 项目结构
```text
├── extension/           # 浏览器插件 (悬浮球、Popup、Gatekeeper Core)
├── server/              # 后端服务中心
│   ├── agents/          # 智能体逻辑 (Gatekeeper - Gemini)
│   ├── chroma_db/       # 向量数据库持久化文件
│   ├── main.py          # FastAPI 服务入口
│   ├── mcp_server.py    # MCP 接口实现
│   └── requirements.txt
├── tools/               # 实用脚本 (watch_memory.py)
├── install.sh           # 环境安装脚本
├── start.sh             # 一键启动服务
└── stop.sh              # 停止所有服务 (带安全检查)
```

## 🚀 快速开始

### 1. 环境配置
创建 `.env` 文件并填入 Google Gemini API Key：
```bash
GEMINI_API_KEY=your_api_key_here
# 可选: 自定义模型
# GATEKEEPER_MODEL=gemini-2.0-flash
```

### 2. 启动记忆中枢 (Server)
```bash
./install.sh  # 首次运行安装依赖
./start.sh    # 启动服务器 (默认端口 8000)
```

### 3. 安装浏览器扩展
1. 打开 Chrome 访问 `chrome://extensions`。
2. 开启 **开发者模式**。
3. 点击 **加载已解压的扩展程序**，选择项目中的 `extension/` 目录。

### 4. 连接 Claude/Cursor (MCP)
**注意**: MCP Server 依赖于后台运行的 FastAPI 服务，请确保已运行 `./start.sh`。

配置 `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "memory-bridge": {
      "command": "/YOUR_ABSOLUTE_PATH/venv/bin/python",
      "args": ["/YOUR_ABSOLUTE_PATH/server/mcp_server.py"]
    }
  }
}
```
*请将 `/YOUR_ABSOLUTE_PATH/` 替换为实际的项目路径。*

## 🤝 贡献
本项目采用 MIT 协议。
