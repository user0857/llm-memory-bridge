# Gemini Memory Bridge

**Gemini Memory Bridge** is a powerful "Second Brain" for your Google Gemini web chats. It bridges the gap between your web interactions and a persistent, local vector database, allowing Gemini to remember facts, preferences, and context across different sessions.

Now featuring a centralized API architecture, allowing both a **Chrome Extension** and an **MCP (Model Context Protocol) Agent** to read/write to the same memory.

![Architecture](./architecture.png)

## ✨ Features

-   **Automatic Memory Capture**:
    -   Saves your inputs and Gemini's responses automatically.
    -   **Smart Filtering**: (Planned) Filters out short/irrelevant chitchat.
-   **Context Injection (RAG)**:
    -   Real-time semantic search as you type.
    -   Injects relevant past memories into the prompt *before* you send it.
-   **Privacy & Control**:
    -   **Pause/Resume**: Global switch in the extension to stop recording.
    -   **Memory Management**: View and delete specific memories directly from the Extension Popup.
    -   **Local First**: All data is stored locally in `ChromaDB`.
-   **MCP Support**:
    -   Connects to Cursor, Claude Desktop, or other MCP clients.
    -   Provides tools: `search_memory`, `save_memory`, `delete_memory`.

## 🛠 Architecture

The project consists of three parts:

1.  **Central Server (FastAPI)**: Manages the ChromaDB vector database and provides HTTP APIs (`/api/search`, `/add_memory`, `/api/delete`).
2.  **Chrome Extension**: Injects into `gemini.google.com`, communicates with the server, handles UI overlay, and captures chat content.
3.  **MCP Server**: A lightweight bridge that allows LLM agents (like Claude or Cursor's AI) to access the same memory database via the Central Server.

## 🚀 Installation & Setup

### Prerequisites
-   Python 3.10+
-   Google Chrome / Brave / Edge

### 1. Start the Central Server
```bash
# 1. Install dependencies
./install.sh

# 2. Start the server (runs in background)
./start.sh
```
*The server runs on `http://127.0.0.1:8000`.*

### 2. Install the Chrome Extension
1.  Open Chrome and go to `chrome://extensions`.
2.  Enable **Developer mode** (top right).
3.  Click **Load unpacked**.
4.  Select the `extension/` folder in this project.
5.  Visit [gemini.google.com](https://gemini.google.com). You should see a status indicator ("M") in the bottom right.

### 3. Configure MCP (Optional)
If you want to use this memory with Claude Desktop or Cursor:

**For Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`):**
```json
{
  "mcpServers": {
    "gemini-memory": {
      "command": "/absolute/path/to/project/venv/bin/python",
      "args": ["/absolute/path/to/project/server/mcp_server.py"]
    }
  }
}
```

## 📖 Usage Guide

### Extension UI
-   **Status Indicator (Bottom Right)**:
    -   **Green (M+)**: Active, relevant context found.
    -   **Gray (M-)**: Recording paused.
    -   **Red**: Server offline or error.
-   **Popup Panel (Click Extension Icon)**:
    -   **Switch**: Toggle Pause/Resume.
    -   **Memory List**: See the top 3 relevant memories for your current input.
    -   **Delete**: Remove specific memories instantly.

### CLI / Agent
You can also interact via the MCP tools if you are using an AI agent:
-   `save_memory(content, tags)`
-   `search_memory(query)`
-   `delete_memory(memory_id)`

## 🛑 Stopping
```bash
./stop_bridge.sh
```

## 🤝 Contributing
Feel free to fork and submit Pull Requests!

## 📄 License
MIT
