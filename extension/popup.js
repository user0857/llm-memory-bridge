// popup.js - Pure View Component

const pauseSwitch = document.getElementById('pause-switch');
const statusLight = document.getElementById('status-light');
const statusText = document.getElementById('status-text');
const memoryList = document.getElementById('memory-list');
const thresholdSlider = document.getElementById('threshold-slider');
const thresholdValue = document.getElementById('threshold-value');
const body = document.body;

// --- 1. Initialization & State Sync ---

async function init() {
    // Load initial state from storage
    const data = await chrome.storage.local.get(['isPaused', 'threshold', 'currentMemories']);
    
    // UI: Paused
    updatePauseState(!!data.isPaused);
    
    // UI: Threshold
    const threshold = data.threshold || 1.0;
    thresholdSlider.value = threshold;
    thresholdValue.innerText = threshold;

    // UI: Memories (Render immediately from cache)
    renderMemories(data.currentMemories || []);
}

// Listen for updates from Content Script (The Single Source of Truth)
chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local') {
        if (changes.isPaused) updatePauseState(changes.isPaused.newValue);
        if (changes.currentMemories) renderMemories(changes.currentMemories.newValue);
    }
});

// --- 2. UI Actions ---

// Toggle Pause
pauseSwitch.addEventListener('change', () => {
    const isPaused = !pauseSwitch.checked;
    chrome.storage.local.set({ isPaused });
    // Content script listens to storage change, no manual message needed
});

// Slider Change
thresholdSlider.addEventListener('input', () => {
    thresholdValue.innerText = thresholdSlider.value;
});

thresholdSlider.addEventListener('change', async () => {
    const newVal = parseFloat(thresholdSlider.value);
    await chrome.storage.local.set({ threshold: newVal });
    
    // Notify Content Script to re-search immediately
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
        chrome.tabs.sendMessage(tab.id, { action: "updateThreshold" });
    }
});

// --- 3. Render Logic ---

function renderMemories(memories) {
    memoryList.innerHTML = '';
    
    if (!memories || memories.length === 0) {
        memoryList.innerHTML = '<p style="font-size: 12px; color: #999;">No relevant context found.</p>';
        return;
    }

    memories.forEach(item => {
        const div = document.createElement('div');
        div.className = 'memory-item';
        
        // Format distance
        const distDisplay = (item.distance !== undefined) ? item.distance.toFixed(3) : "N/A";
        
        div.innerHTML = `
            <div class="content">${item.content}</div>
            <div class="actions">
                <span style="font-size: 10px; color: #999; margin-right: auto;">Dist: ${distDisplay}</span>
                <span class="btn-del" data-id="${item.id}">Delete</span>
            </div>
        `;
        
        // Expand on click
        div.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-del')) return;
            div.classList.toggle('expanded');
        });

        // Delete Action
        div.querySelector('.btn-del').addEventListener('click', async (e) => {
            const id = e.target.dataset.id;
            // Optimistic UI update (optional, but let's wait for sync for correctness)
            div.style.opacity = '0.5'; 
            div.querySelector('.btn-del').innerText = 'Deleting...';
            
            // Delegate to Content Script via Message
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tab) {
                chrome.tabs.sendMessage(tab.id, { action: "deleteMemory", memoryId: id });
            }
        });

        memoryList.appendChild(div);
    });
}

function updatePauseState(isPaused) {
    pauseSwitch.checked = !isPaused;
    if (isPaused) {
        body.className = 'state-paused';
        statusLight.className = 'light gray';
        statusText.innerText = 'Paused';
        memoryList.innerHTML = '<p style="font-size: 12px; color: #999;">Service Paused.</p>';
    } else {
        body.className = 'state-active';
        statusLight.className = 'light green';
        statusText.innerText = 'Ready';
    }
}

// Start
init();
