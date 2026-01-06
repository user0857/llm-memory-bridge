/* content.js - Refactored Structure */

// --- 1. UI Component: Floating Action Button ---
class FabUI {
    constructor(onClickCallback) {
        this.onClick = onClickCallback;
        this.element = null;
        this._init();
    }

    _init() {
        if (document.getElementById('gemini-memory-fab')) return;

        // Create DOM
        this.element = document.createElement("div");
        this.element.id = "gemini-memory-fab";
        this.element.className = "fab-idle";
        this.element.innerText = "M";
        this.element.title = "Memory Bridge Ready";
        
        // Inject CSS
        const style = document.createElement('style');
        style.textContent = `
            #gemini-memory-fab {
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 44px;
                height: 44px;
                border-radius: 50%;
                background-color: #f1f3f4;
                color: #5f6368;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: 'Segoe UI Emoji', 'Apple Color Emoji', sans-serif;
                font-size: 22px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                cursor: default;
                transition: all 0.2s ease;
                z-index: 9999;
                user-select: none;
            }
            #gemini-memory-fab.fab-idle { background-color: #f1f3f4; color: #5f6368; }
            #gemini-memory-fab.fab-searching { background-color: #fff3e0; border: 2px solid #ff9800; cursor: wait; }
            #gemini-memory-fab.fab-thinking { background-color: #f3e5f5; border: 2px solid #9c27b0; cursor: wait; animation: fab-pulse 1.5s infinite; }
            #gemini-memory-fab.fab-ready { 
                background-color: #e8f0fe; 
                border: 2px solid #1a73e8; 
                cursor: pointer; 
                animation: fab-bounce 2s infinite; 
            }
            #gemini-memory-fab.fab-ready:hover { background-color: #d2e3fc; transform: scale(1.05); }

            @keyframes fab-pulse {
                0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(156, 39, 176, 0.4); }
                70% { transform: scale(1.05); box-shadow: 0 0 0 10px rgba(156, 39, 176, 0); }
                100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(156, 39, 176, 0); }
            }
            @keyframes fab-bounce {
                0%, 20%, 50%, 80%, 100% {transform: translateY(0);}
                40% {transform: translateY(-6px);}
                60% {transform: translateY(-3px);}
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(this.element);

        // Events
        this.element.addEventListener('click', () => {
            if (this.element.classList.contains('fab-ready')) {
                this.onClick();
            }
        });
    }

    setState(state) {
        if (!this.element) return;
        this.element.className = '';
        
        switch (state) {
            case 'searching':
                this.element.classList.add('fab-searching');
                this.element.innerText = "👓";
                this.element.title = "Analyzing input...";
                break;
            case 'thinking':
                this.element.classList.add('fab-thinking');
                this.element.innerText = "🧠";
                this.element.title = "Retrieving memories...";
                break;
            case 'ready':
                this.element.classList.add('fab-ready');
                this.element.innerText = "💉";
                this.element.title = "Click to Inject Memory";
                break;
            case 'paused':
                this.element.classList.add('fab-idle');
                this.element.innerText = "M-";
                this.element.title = "Paused";
                break;
            case 'idle':
            default:
                this.element.classList.add('fab-idle');
                this.element.innerText = "M";
                this.element.title = "Memory Bridge Idle";
                break;
        }
    }
}

// --- 2. Logic Controller: Memory Bridge ---
class MemoryBridge {
    constructor() {
        this.isPaused = false;
        this.cachedContext = "";
        this.lastQuery = "";
        this.debounceTimer = null;
        this.fab = new FabUI(() => this.injectContext());
        
        // Response Tracking
        this.lastSavedResponse = "";
        this.aiResponseDebounceTimer = null;
        this.lastCompositionEndTime = 0;
        this.isComposing = false;

        this._initListeners();
        this._syncState();
    }

    _syncState() {
        chrome.storage.local.get(['isPaused'], (result) => {
            this.isPaused = !!result.isPaused;
            this._updateGlobalIcon();
            if (this.isPaused) this.fab.setState('paused');
        });

        chrome.storage.onChanged.addListener((changes, area) => {
            if (area === 'local' && changes.isPaused) {
                this.isPaused = changes.isPaused.newValue;
                this.fab.setState(this.isPaused ? 'paused' : 'idle');
                this._updateGlobalIcon();
            }
        });
    }

    _updateGlobalIcon() {
        const status = this.isPaused ? "gray" : "active";
        try { chrome.runtime.sendMessage({ action: "updateIcon", status: status }); } catch(e){}
    }

    _initListeners() {
        // Listen for requests from Popup (Controller Logic)
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            if (request.action === "deleteMemory") {
                // Proxy Delete via Background
                chrome.runtime.sendMessage({ action: "deleteMemory", memoryId: request.memoryId }, (resp) => {
                    if (resp && resp.success) {
                        this.handleInput(null, 0); // Force Refresh
                    }
                });
            }
            if (request.action === "updateThreshold") {
                this.handleInput(null, 0); // Force Refresh
            }
        });

        // Poll for input area (Gemini loads dynamically)
        setInterval(() => {
            const inputArea = Utils.getInputArea();
            if (inputArea && !inputArea.dataset.bridgeAttached) {
                inputArea.addEventListener("input", (e) => this.handleInput(e, 2000));
                inputArea.addEventListener("paste", () => setTimeout(() => this.handleInput(null, 300), 50));
                inputArea.addEventListener("keydown", (e) => this.handleKeydown(e), true);
                
                inputArea.addEventListener('compositionstart', () => { this.isComposing = true; });
                inputArea.addEventListener('compositionend', () => { 
                    this.isComposing = false; 
                    this.lastCompositionEndTime = Date.now();
                });

                inputArea.dataset.bridgeAttached = "true";
            }
        }, 1000);

        // Listen for AI Responses
        const observer = new MutationObserver((mutations) => this.handleDomMutation(mutations));
        observer.observe(document.body, { childList: true, subtree: true, characterData: true });
    }

    handleInput(e, delay) {
        if (this.isPaused) return;

        const inputArea = Utils.getInputArea();
        if (!inputArea) return;

        const text = inputArea.innerText;
        if (!text || text.trim() === "") {
            this.fab.setState('idle');
            this.cachedContext = "";
            chrome.storage.local.set({ currentMemories: [] });
            return;
        }

        // 1. Searching State
        this.fab.setState('searching');

        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            if (text === this.lastQuery && e !== null) return; // Skip if same query (unless forced by null event)
            this.lastQuery = text;

            // 2. Thinking State
            this.fab.setState('thinking');

            chrome.storage.local.get(['threshold'], (result) => {
                const threshold = result.threshold || 1.0;
                chrome.runtime.sendMessage(
                    { action: "searchContext", query: text, threshold: threshold },
                    (response) => {
                        if (response && response.success) {
                            const results = response.data.results || [];
                            
                            // 1. 本地格式化 Context String (仅取前 5 条注入，保持简洁)
                            const resultsForInjection = results.slice(0, 5);
                            if (resultsForInjection.length > 0) {
                                let formatted = "【本地记忆库提示】:\n";
                                resultsForInjection.forEach(item => {
                                    formatted += `- ${item.content}\n`;
                                });
                                this.cachedContext = formatted.trim();
                                this.fab.setState('ready');
                            } else {
                                this.cachedContext = "";
                                this.fab.setState('idle');
                            }

                            // 2. Sync to Storage for Popup (保存全量 20 条)
                            chrome.storage.local.set({ 
                                currentMemories: results,
                                lastQuery: text 
                            });

                        } else {
                            this.cachedContext = "";
                            chrome.storage.local.set({ currentMemories: [] });
                            this.fab.setState('idle');
                        }
                    }
                );
            });
        }, delay);
    }

    handleKeydown(e) {
        if (this.isPaused) return;
        const timeSinceComposition = Date.now() - this.lastCompositionEndTime;
        if (this.isComposing || timeSinceComposition < 100 || e.isComposing) return;

        // Enter key -> Save User Message (Clean)
        if (e.key === "Enter" && !e.shiftKey) {
            const inputArea = Utils.getInputArea();
            if (!inputArea) return;

            let textToSave = inputArea.innerText;
            if (textToSave && textToSave.trim().length > 0) {
                // Strip injected context
                if (textToSave.includes("【本地记忆库提示】")) {
                    textToSave = textToSave.split("【本地记忆库提示】")[0].trim();
                }
                if (textToSave.length > 0) {
                    chrome.runtime.sendMessage({ action: "addMemory", content: textToSave });
                }
            }
        }
    }

    injectContext() {
        const inputArea = Utils.getInputArea();
        if (!inputArea || !this.cachedContext) return;

        const originalText = inputArea.innerText;
        if (originalText.includes("【本地记忆库提示】")) return;

        inputArea.innerText = originalText + "\n\n" + this.cachedContext;
        inputArea.dispatchEvent(new Event('input', { bubbles: true }));
        Utils.placeCursorAtEnd(inputArea);
        
        this.fab.setState('idle'); // Reset after injection
    }

    handleDomMutation(mutations) {
        if (this.isPaused) return;
        let hasNewText = false;
        for (const mutation of mutations) {
            if (mutation.addedNodes.length > 0 && mutation.target.nodeType === 1) {
                if (mutation.target.getAttribute('contenteditable') === 'true') continue;
                hasNewText = true;
            }
        }
        if (hasNewText) {
            clearTimeout(this.aiResponseDebounceTimer);
            this.aiResponseDebounceTimer = setTimeout(() => this.extractLastAIResponse(), 3000);
        }
    }

    extractLastAIResponse() {
        const targetContainer = Utils.findLastResponseBlock();
        if (targetContainer) {
            const markdownText = Utils.domToMarkdown(targetContainer).trim();
            if (markdownText && markdownText !== this.lastSavedResponse && markdownText.length > 20) {
                this.lastSavedResponse = markdownText;
                chrome.runtime.sendMessage({ action: "addMemory", content: "Gemini: " + markdownText });
            }
        }
    }
}

// --- 3. Utilities ---
const Utils = {
    getInputArea: () => {
        let el = document.querySelector('div.rich-textarea > div[contenteditable="true"]');
        if (el) return el;
        const candidates = document.querySelectorAll('div[contenteditable="true"]');
        for (const c of candidates) {
            if (c.offsetParent !== null && c.clientHeight > 10) return c;
        }
        return document.querySelector('[role="textbox"]');
    },

    placeCursorAtEnd: (el) => {
        el.focus();
        if (typeof window.getSelection != "undefined" && typeof document.createRange != "undefined") {
            const range = document.createRange();
            range.selectNodeContents(el);
            range.collapse(false);
            const sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
        }
    },

    findLastResponseBlock: () => {
        const potentialContainers = document.querySelectorAll('.model-response-text, [data-test-id="model-response-text"]');
        if (potentialContainers.length > 0) {
            return potentialContainers[potentialContainers.length - 1];
        }
        // Fallback heuristic
        const paragraphs = document.querySelectorAll('p');
        for (let i = paragraphs.length - 1; i >= 0; i--) {
             if (!paragraphs[i].closest('[contenteditable="true"]')) {
                 const container = paragraphs[i].closest('div'); 
                 if (container && container.innerText.length > 50) return container;
             }
        }
        return null;
    },

    domToMarkdown: (element) => {
        let md = "";
        for (const node of element.childNodes) {
            if (node.nodeType === Node.TEXT_NODE) {
                md += node.textContent;
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                const tagName = node.tagName.toLowerCase();
                if (tagName === 'pre' || node.classList.contains('code-block')) {
                    md += `\n\n${node.innerText}\n\n`;
                } else if (tagName === 'p') {
                    md += Utils.domToMarkdown(node) + "\n\n";
                } else if (tagName === 'li') {
                    md += "- " + Utils.domToMarkdown(node) + "\n";
                } else {
                    md += Utils.domToMarkdown(node);
                }
            }
        }
        return md;
    }
};

// --- 4. Bootstrap ---
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => new MemoryBridge());
} else {
    new MemoryBridge();
}
