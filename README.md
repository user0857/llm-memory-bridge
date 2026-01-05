# LLM Memory Bridge (ContextMesh)

> "基于 MCP 的全域记忆中枢：打破本地 CLI 与 Web LLM 应用的上下文孤岛。"

**LLM Memory Bridge** (原名 Gemini Memory Bridge) 是一个开源项目，旨在消除本地开发环境与浏览器端 AI 聊天之间的**上下文隔阂 (Context Silos)**。

通过将 **本地向量数据库 (ChromaDB)** 与 **模型上下文协议 (MCP)** 相结合，本项目构建了一个持久化、共享的记忆流。无论你是在终端 (CLI) 中调试代码，还是在网页端 (如 Gemini/ChatGPT) 头脑风暴，你的 AI 助手都能保持**连续、同步的上下文状态**。

## ✨ 核心特性

*   **🔌 全渠道同步 (Omni-channel Sync)**: 通过定制的 Chrome 插件，无缝同步 CLI 工具与 Web LLM 之间的上下文。
*   **⚡ MCP 原生架构**: 将 RAG 能力封装为标准的 MCP 工具 (`search_memory`, `save_memory`)，确保完美兼容 **Claude Desktop**、**Google Gemini CLI** 以及其他 MCP 客户端。
*   **🔒 本地隐私优先 (Local-First)**: 所有记忆向量均存储在本地 ChromaDB 中，确保数据主权。记忆服务本身无需任何 API Key，完全离线运行。

## 🚀 快速开始

### 1. 安装项目

```bash
# 1. 克隆仓库
git clone https://github.com/yourname/llm-memory-bridge.git
cd llm-memory-bridge

# 2. 安装依赖 (Mac/Linux)
chmod +x install.sh
./install.sh
```

### 2. 连接到 Agent (MCP 客户端)

你可以将此 Bridge 连接到任何支持 MCP 的客户端。以下是两种最流行的连接方式：

#### 方案 A: 官方 Google Gemini CLI (推荐)

1.  **安装 Gemini CLI**:
    ```bash
    npm install -g @google/gemini-cli
    ```
2.  **注册 Bridge 服务**:
    ```bash
    gemini mcp add llm-memory-bridge \
      --command "$(pwd)/venv/bin/python" \
      --args "$(pwd)/server/mcp_server.py" \
      --env "PYTHONPATH=$(pwd)/server"
    ```
3.  **开始使用**:
    ```bash
    export GEMINI_API_KEY="你的_API_KEY"
gemini
> /mcp list  # 验证连接状态
> Please remember that my project 'Beacon' is based on ESP32.
```

#### 方案 B: Claude Desktop

将以下配置添加到你的 `claude_desktop_config.json` 文件中 (macOS 上通常位于 `~/Library/Application Support/Claude/`):

```json
{
  "mcpServers": {
    "llm-memory-bridge": {
      "command": "/你的项目的绝对路径/llm-memory-bridge/venv/bin/python",
      "args": [
        "/你的项目的绝对路径/llm-memory-bridge/server/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/你的项目的绝对路径/llm-memory-bridge/server"
      }
    }
  }
}
```

### 3. 安装 Chrome 插件 (用于 Web 同步)

如果你希望将网页端的对话 (如 `gemini.google.com`) 同步到本地记忆库：

1.  打开 Chrome 浏览器，访问 `chrome://extensions/`。
2.  开启右上角的 **Developer mode (开发者模式)**。
3.  点击 **Load unpacked**，选择本项目下的 `extension/` 文件夹。
4.  **启动 Bridge Server** (插件需要此 HTTP 服务来传输数据):
    ```bash
    ./start_bridge.sh
    ```

## 🛠️ 可用的 MCP 工具

连接成功后，你的 AI Agent 将自动获得以下能力：

*   **`search_memory(query: str)`**
    *   *描述*: 对本地长效向量历史进行语义搜索。
    *   *场景*: 当你询问过去的项目、偏好或具体细节时，Agent 会自动调用此工具 (例如："我昨天给你看的那个错误日志是啥？")。
    
*   **`save_memory(content: str, tags: List[str])`**
    *   *描述*: 将信息持久化存储到本地 ChromaDB。
    *   *场景*: 当你明确要求记住某事，或 Agent 识别到重要上下文时自动调用 (例如："记住，这个仓库我用的是 Python 3.11")。

## 📝 使用范例

**场景 1: 教会 AI (写入记忆)**
> **用户**: "我正在做一个新项目叫 'Titan'，它是一个基于 Rust 的 Web 服务器。"
> **Agent**: *思考中... 决定调用 `save_memory("Project Titan: Rust-based web server", ["project", "titan"])`*
> **Agent**: "收到了，我已经把 'Titan' 项目的信息存入记忆库了。"

**场景 2: 唤起记忆 (读取上下文)**
> **用户**: "帮我给 Titan 生成一个 Dockerfile。"
> **Agent**: *思考中... 不知道 Titan 是啥，决定调用 `search_memory("Titan project language framework")`*
> **Agent**: *读取记忆返回结果: "Titan is a Rust-based web server"*
> **Agent**: "根据记忆，Titan 是一个 Rust 项目。这是一个为你优化的 Rust Dockerfile..."

## 🛠️ 架构说明

*   **`server/mcp_server.py`**: 核心 MCP 服务器 (基于 FastMCP)，处理工具请求和 RAG 逻辑。
*   **`server/main.py`**: HTTP 桥接服务，专供 Chrome 插件将网页数据推送到 ChromaDB。
*   **`extension/`**: Chrome 浏览器插件，用于捕获网页聊天上下文。
*   **`chroma_db/`**: 本地向量存储 (隐私保护)。

## License

MIT