# LLM Memory Bridge (记忆神经中枢)

**LLM Memory Bridge** 是一个打通浏览器 AI 对话与本地长期记忆库的“神经桥梁”。它让 Google Gemini 等 Web AI 拥有跨会话的记忆能力，并支持通过 MCP (Model Context Protocol) 供 Claude Desktop 等 Agent 调用。

![架构图](./architecture.png)

## ✨ 核心特性

### 🧠 本地记忆增强 (RAG)
- **智能感知**: 浏览器插件通过悬浮球 (FAB) 实时感知输入内容。
- **动态检索**: 打字即搜索 (Debounce)，自动寻找最相关的历史记忆。
- **状态反馈**: 
    - 👓 **Searching**: 正在理解你的输入。
    - 🧠 **Thinking**: 正在大脑中检索。
    - 💉 **Ready**: 记忆就绪，点击即可一键注入。

### 🔄 全链路同步 (Unified Sync)
- **单源架构**: Content Script 作为唯一数据源，Popup 面板实时同步，杜绝“删了还在”的幽灵数据。
- **双向管理**: 支持在网页端注入，在 Popup 端管理（删除/调整检索阈值）。

### 🔌 MCP 协议支持
- 完美兼容 **Claude Desktop**, **Cursor** 等支持 MCP 的 AI 客户端。
- **工具集**:
    - `search_memory`: 语义检索。
    - `save_memory`: 智能存储（总结后存入）。
    - `update_memory`: 纠错与更新。
    - `delete_memory`: 遗忘与清理。

## 🛠 技术栈
- **Backend**: FastAPI, ChromaDB (Vector Store), Sentence-Transformers (Local Embedding).
- **Frontend**: Chrome Extension (Vanilla JS, CSS Variables, Content-Script-Driven Architecture).
- **Protocol**: Model Context Protocol (FastMCP).

## 🚀 快速开始

### 1. 启动记忆中枢 (Server)
```bash
# 安装依赖
./install.sh

# 启动服务 (运行在 http://127.0.0.1:8000)
./start.sh
```

### 2. 安装浏览器触手 (Extension)
1. 打开 Chrome 访问 `chrome://extensions`。
2. 开启 **开发者模式**。
3. 点击 **加载已解压的扩展程序**。
4. 选择本项目中的 `extension/` 目录。
5. 刷新 Gemini 页面，你应该能看到右下角的 "M" 悬浮球。

### 3. 连接 AI Agent (可选)
配置 Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "memory-bridge": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": ["/absolute/path/to/server/mcp_server.py"]
    }
  }
}
```

## 📖 使用指南

- **日常对话**: 在网页输入框打字，看到 💉 亮起时，点击即可注入记忆上下文。
- **记忆管理**: 点击浏览器右上角插件图标，可查看最近检索到的记忆，支持删除或调整相关度阈值 (0.5 - 1.5)。
- **Agent 交互**: 对 Claude 说 "记住我们决定用 FastAPI"，它会自动调用 `save_memory`。

## 🤝 贡献
本项目采用 MIT 协议。欢迎提交 PR 增强本地模型的推理能力 (WebLLM Integration)。