// popup.js - Pure View Component

const statusLight = document.getElementById('status-light');
const statusText = document.getElementById('status-text');
const memoryList = document.getElementById('memory-list');
const searchInput = document.getElementById('search-input');
const body = document.body;

// --- 1. Initialization & State Sync ---

async function init() {
    setAppState('offline'); // Default start
    
    // Check Server Health
    const isServerUp = await checkServer();
    if (isServerUp) {
        setAppState('online');
    } else {
        setAppState('offline');
        memoryList.innerHTML = '<p style="font-size: 12px; color: #999;">Server unavailable. Make sure "start.sh" is running.</p>';
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
    memoryList.innerHTML = '<p style="font-size: 12px; color: #666;">Searching...</p>';
    
    try {
        const response = await fetch('http://localhost:8000/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_input: query, n_results: 10 })
        });
        
        if (!response.ok) throw new Error('Search failed');
        
        const data = await response.json();
        renderMemories(data.results || []);
        setAppState('online'); // Search done -> Green
        
    } catch (err) {
        console.error(err);
        memoryList.innerHTML = `<p style="font-size: 12px; color: var(--status-red);">Error: ${err.message}</p>`;
        setAppState('online'); // Revert to green (or maybe error state?)
    }
}

// --- 3. View State Management ---

function setAppState(state) {
    // Reset classes
    body.className = '';
    statusLight.className = 'light';
    statusLight.removeAttribute('style');
    
    switch (state) {
        case 'offline':
            body.classList.add('state-offline');
            statusLight.classList.add('gray');
            statusText.innerText = 'Offline';
            break;
        case 'online':
            body.classList.add('state-online');
            statusLight.classList.add('green');
            statusText.innerText = 'Success';
            break;
        case 'searching':
            body.classList.add('state-searching');
            statusLight.classList.add('blue');
            statusText.innerText = 'Processing...';
            break;
    }
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
    let link = null;

    if (source === 'web_extension') {
        icon = '🌐';
        label = 'Web';
        if (url) link = url;
    } else if (source === 'cli' || source === 'mcp') {
        icon = '💻';
        label = 'CLI';
    }

    let html = `<span title="${source}">${icon} ${label}</span>`;
    if (link) {
        html = `<a href="${link}" target="_blank" style="text-decoration:none; color:inherit;">${html}</a>`;
    }
    return html;
}

function renderMemories(memories) {
    memoryList.innerHTML = '';
    
    if (!memories || memories.length === 0) {
        memoryList.innerHTML = '<p style="font-size: 12px; color: #999;">No relevant context found.</p>';
        return;
    }

    memories.forEach(item => {
        const div = document.createElement('div');
        div.className = 'memory-item';
        
        // Metadata access (handle structure variations)
        const meta = item.metadata || {};
        const timestamp = meta.timestamp || item.timestamp;
        const source = meta.source || 'unknown';
        const sourceUrl = meta.source_url || null;

        // Format distance
        const distDisplay = (item.distance !== undefined) ? item.distance.toFixed(3) : "";
        
        div.innerHTML = `
            <div class="content">${item.content}</div>
            <div class="meta-footer">
                <div class="meta-left">
                    ${formatSource(source, sourceUrl)}
                    <span class="meta-sep">•</span>
                    <span>${formatTime(timestamp)}</span>
                </div>
                <div class="actions">
                    <span style="font-size: 9px; color: #ccc; margin-right: 6px;">${distDisplay}</span>
                    <span class="btn-del" data-id="${item.id}">Delete</span>
                </div>
            </div>
        `;
        
        // Expand on click
        div.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-del') || e.target.closest('a')) return;
            div.classList.toggle('expanded');
        });

        // Delete Action
        div.querySelector('.btn-del').addEventListener('click', async (e) => {
            const id = e.target.dataset.id;
            // Optimistic UI update
            div.style.opacity = '0.5'; 
            div.querySelector('.btn-del').innerText = '...';
            
            try {
                await fetch('http://localhost:8000/api/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ memory_id: id })
                });
                div.remove();
            } catch (err) {
                div.style.opacity = '1';
                div.querySelector('.btn-del').innerText = 'Error';
            }
        });

        memoryList.appendChild(div);
    });
}

// Start
init();
