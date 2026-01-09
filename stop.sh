#!/bin/bash

# --- 配置 ---
PORT=8000
# 定义进程特征签名，确保只杀自己人
SERVER_SIGNATURE="server.main:app"
WATCHER_SIGNATURE="tools/watch_memory.py"

SERVER_PID_FILE="server.pid"
WATCHER_PID_FILE="watcher.pid"

echo "🛑 Stopping services with safety checks..."

# --- 函数: 安全查杀 ---
safe_kill_by_port() {
    local port=$1
    local signature=$2
    
    # 找出占用端口的 PID
    local pids=$(lsof -t -i:$port 2>/dev/null)
    
    if [ -z "$pids" ]; then
        echo "   - Port $port is free."
        return
    fi

    for pid in $pids; do
        # 获取该 PID 的完整运行命令
        local cmd=$(ps -p $pid -o command=)
        
        # 检查命令中是否包含我们的特征签名
        if [[ "$cmd" == *"$signature"* ]]; then
            echo "   - ✅ Verified target (PID: $pid): $cmd"
            echo "   - Killing..."
            kill -9 $pid 2>/dev/null
        else
            echo "   - ⚠️  WARNING: Port $port is in use by a DIFFERENT process (PID: $pid)."
            echo "   - Command: $cmd"
            echo "   - SKIPPING kill to prevent accidental damage."
        fi
    done
}

safe_kill_by_name() {
    local signature=$1
    # pgrep -f -l 可以显示 PID 和 命令行，用于二次确认（这里直接用 pgrep -f 配合 ps）
    local pids=$(pgrep -f "$signature")
    
    if [ -z "$pids" ]; then
        echo "   - No process found matching '$signature'."
        return
    fi

    for pid in $pids; do
        # 排除掉当前这个 stop.sh 脚本自己 (防止误判)
        if [ "$pid" == "$$" ]; then continue; fi
        
        echo "   - Killing Watcher (PID: $pid)..."
        kill -9 $pid 2>/dev/null
    done
}

# 1. 尝试停止 Server (带身份验证)
safe_kill_by_port $PORT "$SERVER_SIGNATURE"

# 2. 尝试停止 Watcher (带身份验证)
safe_kill_by_name "$WATCHER_SIGNATURE"

# 3. 清理 PID 文件
rm -f "$SERVER_PID_FILE" "$WATCHER_PID_FILE"

echo "✅ Stop sequence complete."
