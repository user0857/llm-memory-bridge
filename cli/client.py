import os
import sys
import asyncio
import google.generativeai as genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pathlib import Path

# --- 配置 ---
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("❌ 错误: 未找到 GEMINI_API_KEY 环境变量。")
    sys.exit(1)

genai.configure(api_key=API_KEY)

# --- MCP Client Context Manager ---
class McpClientContext:
    def __init__(self):
        # 自动定位 mcp_server.py
        current_dir = Path(__file__).parent
        server_path = current_dir.parent / "server" / "mcp_server.py"
        
        self.server_params = StdioServerParameters(
            command="python3", # 假设 python3 在 PATH 中，或者使用 sys.executable
            args=[str(server_path)],
            env={
                "PYTHONPATH": str(server_path.parent),
                "GEMINI_API_KEY": API_KEY, # 传递 key 给 server (如果有需要)
                "PATH": os.environ.get("PATH", "")
            }
        )
        self.session = None
        self.exit_stack = None

    async def __aenter__(self):
        self.exit_stack = contextlib.AsyncExitStack()
        read, write = await self.exit_stack.enter_async_context(stdio_client(self.server_params))
        self.session = await self.exit_stack.enter_async_context(ClientSession(read, write))
        await self.session.initialize()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.exit_stack.aclose()

    async def get_tools_for_gemini(self):
        """
        动态获取 MCP 工具并转换为 Gemini SDK 可用的格式
        """
        mcp_tools = await self.session.list_tools()
        gemini_tools = []
        
        for tool in mcp_tools.tools:
            # 为每个工具创建一个闭包函数
            # Gemini SDK 需要函数有明确的 Docstring
            
            tool_name = tool.name
            tool_desc = tool.description
            
            # 动态生成函数
            async def dynamic_tool_func(**kwargs):
                # print(f"  🛠️  [MCP Call] {tool_name}({kwargs})")
                result = await self.session.call_tool(tool_name, arguments=kwargs)
                if result.isError:
                    return f"Error: {result.content}"
                return result.content[0].text if result.content else "Success"
            
            # 必须重命名函数，否则 Gemini 看到的都是 "dynamic_tool_func"
            dynamic_tool_func.__name__ = tool_name
            dynamic_tool_func.__doc__ = tool_desc
            
            gemini_tools.append(dynamic_tool_func)
            
        return gemini_tools

import contextlib

# --- 主程序 ---
async def main():
    print("🔌 Connecting to MCP Server...")
    
    async with McpClientContext() as mcp_ctx:
        # 1. 获取动态工具
        tools = await mcp_ctx.get_tools_for_gemini()
        print(f"✅ Connected! Loaded {len(tools)} tools: {[t.__name__ for t in tools]}")
        
        # 2. 初始化 Gemini
        # 注意: 目前 Gemini Python SDK 的 Function Calling 对异步函数的支持
        # 可能需要适配。最好的方式是将工具列表传给 model，让 SDK 知道它们的存在。
        # 这里的 dynamic_tool_func 是 async 的，SDK 0.8.3+ 应该能处理，
        # 或者我们手动处理 function_call。
        
        # 为了兼容性，Gemini SDK 的 enable_automatic_function_calling 
        # 目前主要设计给同步函数。我们这里做一个简单的同步包装器可能更稳妥，
        # 但因为我们需要 await session.call_tool，所以必须在一个 async 循环里。
        
        # 临时方案：Gemini SDK 的自动模式可能不支持 async 工具。
        # 我们这里使用手动工具调用模式 (Manual Function Calling) 会更稳健。
        
        model = genai.GenerativeModel('gemini-1.5-flash', tools=tools)
        chat = model.start_chat(enable_automatic_function_calling=True) 
        # 尝试开启自动模式，如果报错，说明 SDK 还不支持 async tools
        
        print("\n🤖 Gemini CLI (MCP Native Mode)")
        print("-------------------------------------")
        print("提示: 我已连接到本地记忆神经中枢。")

        while True:
            try:
                # 异步获取输入，避免阻塞事件循环
                loop = asyncio.get_running_loop()
                user_input = await loop.run_in_executor(None, input, "\nYou: ")
                
                if user_input.strip().lower() in ['exit', 'quit']: 
                    break
                
                # 发送消息
                # 注意: send_message_async 是异步方法
                response = await chat.send_message_async(user_input)
                print(f"Gemini: {response.text}")

            except Exception as e:
                print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
