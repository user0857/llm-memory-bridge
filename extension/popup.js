// popup.js

const API_BASE = "http://127.0.0.1:8000";

const pauseSwitch = document.getElementById('pause-switch');
const statusLight = document.getElementById('status-light');
const statusText = document.getElementById('status-text');
const memoryList = document.getElementById('memory-list');
const body = document.body;

// 1. 初始化状态
chrome.storage.local.get(['isPaused'], (result) => {
    const isPaused = !!result.isPaused;
    pauseSwitch.checked = !isPaused;
    updateUIState(isPaused);
    if (!isPaused) {
        fetchRelevantMemories();
    }
});

// 2. 监听开关
pauseSwitch.addEventListener('change', () => {
    const isPaused = !pauseSwitch.checked;
    chrome.storage.local.set({ isPaused });
    updateUIState(isPaused);
    if (isPaused) {
        memoryList.innerHTML = '<p style="font-size: 12px; color: #999;">Service Paused.</p>';
    } else {
        fetchRelevantMemories();
    }
});

function updateUIState(isPaused) {
    if (isPaused) {
        body.className = 'state-paused';
        statusLight.className = 'light gray';
        statusText.innerText = 'Paused';
    } else {
        body.className = 'state-active';
        statusLight.className = 'light green';
        statusText.innerText = 'Ready';
    }
}

// 3. 获取相关记忆
async function fetchRelevantMemories() {
    setStatus('processing', 'Searching...');
    
    try {
        // 获取当前活动标签页的输入内容
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab || !tab.url.includes("gemini.google.com")) {
            setStatus('active', 'Ready (Not on Gemini)');
            memoryList.innerHTML = '<p style="font-size: 12px; color: #999;">Open Gemini to see relevant context.</p>';
            return;
        }

        // 向 content.js 请求当前输入框文本
        chrome.tabs.sendMessage(tab.id, { action: "getCurrentInput" }, async (response) => {
            const query = (response && response.text) ? response.text : "";
            
            // 调用后端搜索
            const searchResp = await fetch(`${API_BASE}/api/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_input: query || "最近的记忆" }) // 如果没输入，搜一下最近的
            });

            if (!searchResp.ok) throw new Error("Server Offline");
            
            const data = await searchResp.json();
            renderMemories(data.results || []);
            setStatus('active', 'Ready');
        });

    } catch (err) {
        console.error(err);
        setStatus('error', 'Server Error');
    }
}

function setStatus(state, text) {
    statusText.innerText = text;
    if (state === 'processing') {
        statusLight.className = 'light processing';
    } else if (state === 'error') {
        statusLight.className = 'light red';
        body.className = 'state-error';
    } else {
        // 根据暂停状态恢复
        chrome.storage.local.get(['isPaused'], (result) => {
            updateUIState(!!result.isPaused);
        });
    }
}

function renderMemories(items) {
    if (items.length === 0) {
        memoryList.innerHTML = '<p style="font-size: 12px; color: #999;">No relevant context found.</p>';
        return;
    }

    memoryList.innerHTML = '';
    items.slice(0, 3).forEach(item => {
        const div = document.createElement('div');
        div.className = 'memory-item';
        div.innerHTML = `
            <div class="content">${item.content}</div>
            <div class="actions">
                <span class="btn-del" data-id="${item.id}">Delete</span>
            </div>
        `;
        
        // 点击展开/收起
        div.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-del')) return;
            div.classList.toggle('expanded');
        });

        // 删除逻辑
        div.querySelector('.btn-del').addEventListener('click', async (e) => {
            const id = e.target.dataset.id;
            setStatus('processing', 'Deleting...');
            try {
                const resp = await fetch(`${API_BASE}/api/delete`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ memory_id: id })
                });
                if (resp.ok) {
                    div.remove();
                    setStatus('active', 'Deleted');
                    setTimeout(() => setStatus('active', 'Ready'), 1500);
                }
            } catch (err) {
                setStatus('error', 'Delete Failed');
            }
        });

        memoryList.appendChild(div);
    });
}
