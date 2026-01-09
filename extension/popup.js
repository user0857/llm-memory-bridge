// popup.js - Modern Logic

const statusBadge = document.getElementById('status-badge');
const statusText = statusBadge.querySelector('.status-text');
const memoryList = document.getElementById('memory-list');
const searchInput = document.getElementById('search-input');

// --- 1. Initialization & State Sync ---

async function init() {
    setAppState('offline'); // Default start
    
    // Check Server Health
    const isServerUp = await checkServer();
    if (isServerUp) {
        setAppState('online');
    } else {
        setAppState('offline');
        renderEmpty('Server unavailable. Check start.sh');
        return; 
    }

    // Load initial memories from storage (Context)
    const data = await chrome.storage.local.get(['currentMemories']);
    renderMemories(data.currentMemories || []);
}

// Listen for updates from Content Script
chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local') {
        // Only update memories from storage if user hasn't searched manually
        if (changes.currentMemories && !searchInput.value) {
             renderMemories(changes.currentMemories.newValue);
        }
    }
});

// --- 2. UI Actions ---

async function checkServer() {
    try {
        const res = await fetch('http://localhost:8000/');
        return res.ok;
    } catch (e) {
        return false;
    }
}

// Search Input
searchInput.addEventListener('keyup', async (e) => {
    if (e.key === 'Enter') {
        const query = searchInput.value.trim();
        if (query) {
            await performSearch(query);
        } else {
            // If empty, revert to context memories and Online state
            setAppState('online');
            const data = await chrome.storage.local.get(['currentMemories']);
            renderMemories(data.currentMemories || []);
        }
    }
});

async function performSearch(query) {
    setAppState('searching');
    memoryList.innerHTML = '<div class="empty-state">🔍 Searching...</div>';
    
    try {
        const response = await fetch('http://localhost:8000/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_input: query, n_results: 10 })
        });
        
        if (!response.ok) throw new Error('Search failed');
        
        const data = await response.json();
        renderMemories(data.results || []);
        setAppState('online'); 
        
    } catch (err) {
        console.error(err);
        renderEmpty(`Error: ${err.message}`);
        setAppState('online'); 
    }
}

// --- 3. View State Management ---

function setAppState(state) {
    // Reset base class but keep 'status-badge'
    statusBadge.className = 'status-badge';
    
    switch (state) {
        case 'offline':
            statusBadge.classList.add('offline');
            statusText.innerText = 'Offline';
            break;
        case 'online':
            statusBadge.classList.add('online');
            statusText.innerText = 'Ready';
            break;
        case 'searching':
            statusBadge.classList.add('searching');
            statusText.innerText = 'Thinking...';
            break;
    }
}

function renderEmpty(msg = 'No relevant memories found.') {
    memoryList.innerHTML = `<div class="empty-state">📭 ${msg}</div>`;
}

// --- 4. Render Logic ---

function formatTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.round(diffMs / 1000);
    const diffMin = Math.round(diffSec / 60);
    const diffHr = Math.round(diffMin / 60);
    const diffDay = Math.round(diffHr / 24);

    if (diffSec < 60) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHr < 24) return `${diffHr}h ago`;
    if (diffDay < 7) return `${diffDay}d ago`;
    return date.toLocaleDateString();
}

function formatSource(source, url) {
    let icon = '❓';
    let label = source || 'Unknown';
    let tagClass = 'source-tag';
    
    if (source === 'web_extension' || source === 'web') {
        icon = '🌐';
        label = 'Web';
    } else if (source === 'cli' || source === 'mcp') {
        icon = '💻';
        label = 'CLI';
    } else if (source === 'file_watcher') {
        icon = '📁';
        label = 'File';
    }

    if (url) {
        return `<a href="${url}" class="${tagClass}" target="_blank">${icon} ${label}</a>`;
    } else {
        return `<span class="${tagClass}">${icon} ${label}</span>`;
    }
}

const trashIcon = `<svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>`;
const copyIcon = `<svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;
const checkIcon = `<svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;

function renderMemories(memories) {
    memoryList.innerHTML = '';
    
    if (!memories || memories.length === 0) {
        renderEmpty();
        return;
    }

    memories.forEach((item, index) => {
        const div = document.createElement('div');
        div.className = 'memory-item';
        div.style.animationDelay = `${index * 0.05}s`;
        
        const meta = item.metadata || {};
        const timestamp = meta.timestamp || item.timestamp;
        const source = meta.source || 'unknown';
        const sourceUrl = meta.source_url || null;
        
        div.innerHTML = `
            <div class="content">${item.content}</div>
            <div class="meta-footer">
                <div class="meta-left">
                    ${formatSource(source, sourceUrl)}
                    <span class="time-text">${formatTime(timestamp)}</span>
                </div>
                <div class="actions">
                    <div class="btn-action btn-copy" title="Copy Content">
                        ${copyIcon}
                    </div>
                    <div class="btn-action btn-del" title="Delete Memory" data-id="${item.id}">
                        ${trashIcon}
                    </div>
                </div>
            </div>
        `;
        
        // --- Event Listeners ---

        // Expand/Collapse
        div.addEventListener('click', (e) => {
            if (e.target.closest('.btn-action') || e.target.closest('a')) return;
            div.classList.toggle('expanded');
        });

        // Copy Logic
        const btnCopy = div.querySelector('.btn-copy');
        let copyTimeout;
        btnCopy.addEventListener('click', async (e) => {
            e.stopPropagation();
            
            try {
                await navigator.clipboard.writeText(item.content);
                
                // UI Feedback
                btnCopy.innerHTML = checkIcon;
                btnCopy.classList.add('copied');
                
                // Revert after 2s
                if (copyTimeout) clearTimeout(copyTimeout);
                copyTimeout = setTimeout(() => {
                    btnCopy.innerHTML = copyIcon;
                    btnCopy.classList.remove('copied');
                }, 2000);
                
            } catch (err) {
                console.error('Failed to copy!', err);
            }
        });

        // Delete Logic
        const btnDel = div.querySelector('.btn-del');
        btnDel.addEventListener('click', async (e) => {
            e.stopPropagation();
            const id = btnDel.dataset.id;
            
            div.style.transition = 'opacity 0.2s, transform 0.2s';
            div.style.opacity = '0';
            div.style.transform = 'scale(0.9)';
            
            try {
                await fetch('http://localhost:8000/api/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ memory_id: id })
                });
                setTimeout(() => div.remove(), 200);
            } catch (err) {
                div.style.opacity = '1';
                div.style.transform = 'scale(1)';
                alert('Delete failed');
            }
        });

        memoryList.appendChild(div);
    });
}

// Start
init();