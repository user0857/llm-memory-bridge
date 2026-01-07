# LLM Memory Bridge (记忆神经中枢)

**LLM Memory Bridge** 是一个打通浏览器 AI 对话与本地长期记忆库的“神经桥梁”。它让 Google Gemini 等 Web AI 拥有跨会话的记忆能力，并支持通过 MCP (Model Context Protocol) 供 Claude Desktop 等 Agent 调用。

本项目目前已全面迁移至 **MLX** 框架，在 macOS 上实现极致的本地模型推理。

![架构图](./architecture.png)

## ✨ 核心特性

### 🧠 本地智能体：Librarian (图书管理员)
- **极速推理**: 基于 Apple **MLX** 框架，直接在本地 GPU 运行 `Youtu-LLM-2B`。
- **意图识别**: 智能判断输入是需要“保存”、“更新”还是“忽略”，防止记忆库被垃圾信息污染。
- **自动摘要**: 自动对长网页内容或聊天片段进行提炼和打标签。

### 👓 浏览器感知 (RAG)
- **智能感知**: 浏览器插件通过悬浮球 (FAB) 实时感知输入内容。
- **动态检索**: 自动从 ChromaDB 向量库中寻找相关历史，并在就绪时提供注入。

### 🔌 MCP 协议支持
- 完美兼容 **Claude Desktop**, **Cursor** 等 AI 客户端。
- **工具集**:
    - `search_memory`: 语义检索。
    - `save_memory`: 智能存储（经过 Librarian 总结）。
    - `update_memory`: 结合上下文更新旧记忆。
    - `delete_memory`: 遗忘与清理。

## 🛠 技术栈
- **推理引擎**: [MLX LM](https://github.com/ml-explore/mlx-examples/tree/main/llms) (Apple Silicon 优化)。
- **核心模型**: `Youtu-LLM-2B-4bit` (国产 2B 参数量级佼佼者)。
- **Backend**: FastAPI, ChromaDB (向量库), Sentence-Transformers (嵌入模型)。
- **Frontend**: Chrome Extension (Vanilla JS, Content-Script-Driven)。

## 📂 项目结构
```text
├── extension/           # 浏览器插件 (悬浮球、Popup、背景脚本)
├── models/              # 本地模型权重 (.gguf 或 mlx 权重)
├── server/              # 后端服务中心
│   ├── agents/          # 智能体逻辑 (Librarian)
│   ├── chroma_db/       # 向量数据库持久化文件
│   ├── main.py          # FastAPI 服务入口
│   ├── mcp_server.py    # MCP 接口实现
│   └── requirements.txt
├── start.sh             # 一键启动服务
└── stop.sh              # 停止所有服务
```

## 🚀 快速开始

### 1. 启动记忆中枢 (Server)
确保你使用的是 Apple Silicon 芯片，并安装了依赖：
```bash
./install.sh
./start.sh
```

### 2. 安装浏览器扩展
1. 打开 Chrome 访问 `chrome://extensions`。
2. 开启 **开发者模式**。
3. 点击 **加载已解压的扩展程序**，选择项目中的 `extension/` 目录。
4. 在 Gemini 页面右下角即可看到 "Librarian" 的状态球。

### 3. 连接 Claude/Cursor (MCP)
配置 `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "memory-bridge": {
      "command": "/YOUR_PATH/venv/bin/python",
      "args": ["/YOUR_PATH/server/mcp_server.py"]
    }
  }
}
```

## 🤝 贡献
本项目采用 MIT 协议。欢迎提交 PR 增强本地模型的 Agent 决策能力。
