# LLM Memory Bridge (ContextMesh)

> "A unified, local-first context layer bridging the gap between CLI Agents and Web-based LLM interactions via MCP and Browser Extensions."

**LLM Memory Bridge** (formerly Gemini Memory Bridge) is an open-source initiative designed to dismantle the **context silos** between your local development environment and browser-based AI chats.

By orchestrating a **local vector store (ChromaDB)** with the **Model Context Protocol (MCP)**, this project creates a persistent, shared memory stream. Whether you are debugging via a terminal CLI or brainstorming in a web interface (e.g., Gemini/ChatGPT), your AI assistant maintains a **continuous, synchronized state**.

## ✨ Key Features

*   **🔌 Omni-channel Synchronization**: Seamlessly syncs context between CLI tools and Web LLMs using a custom Chrome Extension.
*   **⚡ MCP-Native Architecture**: Exposes RAG capabilities as standard MCP tools (`search_memory`, `save_memory`), ensuring compatibility with Claude Desktop, Cursor, and other MCP clients.
*   **🔒 Local-First Privacy**: All memory vectors are stored locally in ChromaDB, ensuring data sovereignty.
*   **🧠 Autonomous Agent**: Includes a built-in Gemini Agent tool that can autonomously research your memory bank to answer complex queries.

## 🚀 Quick Start

### 1. Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourname/llm-memory-bridge.git
cd llm-memory-bridge

# 2. Install dependencies (Mac/Linux)
chmod +x install.sh
./install.sh
```

### 2. Configure MCP Client (e.g., Claude Desktop)

To use the memory tools within **Claude Desktop** or other MCP-compliant apps, add the following configuration to your settings file (typically `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "llm-memory-bridge": {
      "command": "/usr/bin/python3",
      "args": [
        "/ABSOLUTE/PATH/TO/llm-memory-bridge/server/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/ABSOLUTE/PATH/TO/llm-memory-bridge/server",
        "GEMINI_API_KEY": "your_gemini_api_key_here" 
      }
    }
  }
}
```
*Note: Replace `/ABSOLUTE/PATH/TO/...` with the actual full path to your project directory.*

### 3. Install Chrome Extension (for Web Sync)

1.  Open Chrome and navigate to `chrome://extensions/`.
2.  Enable **Developer mode** in the top right.
3.  Click **Load unpacked** and select the `extension/` directory in this project.
4.  **Start the Bridge Server** (Required for the extension to work):
    ```bash
    ./start_bridge.sh
    ```

### 4. Usage

#### In Claude Desktop (MCP Mode)
Simply ask Claude natural language questions. It will use the tools automatically:
*   *"What was the project code name I mentioned yesterday?"* -> Calls `search_memory`
*   *"Remember that I prefer TypeScript for frontend."* -> Calls `save_memory`
*   *"Ask Gemini to summarize the project history."* -> Calls `chat_with_gemini`

#### In Browser (Web Sync Mode)
Just use `gemini.google.com` as usual. The extension will automatically sync your conversations to the local memory, making them available to your CLI/MCP agents instantly.

## 🛠️ Architecture

*   **`server/mcp_server.py`**: The core MCP server handling tool requests and RAG logic.
*   **`server/main.py`**: HTTP bridge for the Chrome Extension.
*   **`extension/`**: Captures web context and syncs to the local bridge.
*   **`chroma_db/`**: Local vector storage.

## License

MIT