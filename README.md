# LLM Memory Bridge (ContextMesh)

> "A unified, local-first context layer bridging the gap between CLI Agents and Web-based LLM interactions via MCP and Browser Extensions."

**LLM Memory Bridge** (formerly Gemini Memory Bridge) is an open-source initiative designed to dismantle the **context silos** between your local development environment and browser-based AI chats.

By orchestrating a **local vector store (ChromaDB)** with the **Model Context Protocol (MCP)**, this project creates a persistent, shared memory stream. Whether you are debugging via a terminal CLI or brainstorming in a web interface (e.g., Gemini/ChatGPT), your AI assistant maintains a **continuous, synchronized state**.

## ✨ Key Features

*   **🔌 Omni-channel Synchronization**: Seamlessly syncs context between CLI tools and Web LLMs using a custom Chrome Extension.
*   **⚡ MCP-Native Architecture**: Exposes RAG capabilities as standard MCP tools (`search_memory`, `save_memory`), ensuring compatibility with **Claude Desktop**, **Gemini CLI**, and other MCP clients.
*   **🔒 Local-First Privacy**: All memory vectors are stored locally in ChromaDB, ensuring data sovereignty. No API keys are required for the memory server itself.

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

### 2. Connect to an Agent (MCP Client)

You can connect this bridge to any MCP-compliant client. Here are the two most popular methods:

#### Option A: Official Google Gemini CLI (Recommended)

1.  **Install Gemini CLI**:
    ```bash
    npm install -g @google/gemini-cli
    ```
2.  **Register the Bridge**:
    ```bash
    gemini mcp add llm-memory-bridge \
      --command "$(pwd)/venv/bin/python" \
      --args "$(pwd)/server/mcp_server.py" \
      --env "PYTHONPATH=$(pwd)/server"
    ```
3.  **Use it**:
    ```bash
    export GEMINI_API_KEY="your_api_key"
    gemini
    > /mcp list  # Verify connection
    > Please remember that my project 'Beacon' is based on ESP32.
    ```

#### Option B: Claude Desktop

Add the following to your `claude_desktop_config.json` (typically in `~/Library/Application Support/Claude/` on macOS):

```json
{
  "mcpServers": {
    "llm-memory-bridge": {
      "command": "/ABSOLUTE/PATH/TO/llm-memory-bridge/venv/bin/python",
      "args": [
        "/ABSOLUTE/PATH/TO/llm-memory-bridge/server/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/ABSOLUTE/PATH/TO/llm-memory-bridge/server"
      }
    }
  }
}
```

### 3. Install Chrome Extension (for Web Sync)

To sync your web conversations (e.g., from `gemini.google.com`) into this local memory:

1.  Open Chrome and navigate to `chrome://extensions/`.
2.  Enable **Developer mode** in the top right.
3.  Click **Load unpacked** and select the `extension/` directory in this project.
4.  **Start the Bridge Server** (The extension needs this HTTP bridge):
    ```bash
    ./start_bridge.sh
    ```

## 🛠️ MCP Tools Available

Once connected, your AI Agent will automatically have access to these tools:

*   **`search_memory(query: str)`**
    *   *Description*: Semantic search through your long-term vector history.
    *   *Usage*: The Agent calls this when you ask about past projects, preferences, or specific details (e.g., "What was the error log I showed you yesterday?").
    
*   **`save_memory(content: str, tags: List[str])`**
    *   *Description*: Persist information into the local ChromaDB.
    *   *Usage*: The Agent calls this when you explicitly ask it to remember something or when it detects important context (e.g., "Note that I'm using Python 3.11 for this repo").

## 📝 Usage Examples

**Scenario 1: Teaching the AI**
> **User**: "I'm working on a new project called 'Titan'. It's a Rust-based web server."
> **Agent**: *Thinking... calls `save_memory("Project Titan: Rust-based web server", ["project", "titan"])`*
> **Agent**: "Got it. I've saved 'Titan' to your memory."

**Scenario 2: Recalling Context**
> **User**: "Generate a Dockerfile for Titan."
> **Agent**: *Thinking... calls `search_memory("Titan project language framework")`*
> **Agent**: *Reads memory: "Titan is a Rust-based web server"*
> **Agent**: "Here is a Dockerfile optimized for a Rust application..."

## 🛠️ Architecture

*   **`server/mcp_server.py`**: The core MCP server (FastMCP) handling tool requests and RAG logic.
*   **`server/main.py`**: HTTP bridge for the Chrome Extension to push data to ChromaDB.
*   **`extension/`**: Chrome extension that captures web chat context.
*   **`chroma_db/`**: Local vector storage (Privacy-focused).

## License

MIT
