/* content.js - Browser Librarian Version */

// 使用 IIFE (Immediately Invoked Function Expression) 避免全局污染和重复声明
(function() {

    // 防止重复初始化
    if (window.hasInitializedGeminiMemory) return;
    window.hasInitializedGeminiMemory = true;

    // --- 1. Core Logic: Browser Gatekeeper ---
    class BrowserGatekeeper {
        static async memorize() {
            // 1. Gather Content (Simple Heuristics for now)
            const title = document.title;
            const url = window.location.href;
            const selection = window.getSelection().toString();
            
            let contentToSave = "";
            
            if (selection && selection.length > 10) {
                contentToSave = `[Selection from ${title}]: ${selection}`;
            } else {
                try {
                    // Use Mozilla Readability to extract clean content
                    // We clone the document because Readability is destructive
                    const documentClone = document.cloneNode(true);
                    const reader = new Readability(documentClone);
                    const article = reader.parse();
                    
                    if (article && article.textContent) {
                        // Limit text to a reasonable length for the first pass (e.g., 15k chars)
                        const cleanText = article.textContent.replace(/\s+/g, ' ').trim();
                        contentToSave = `[Full Article from ${article.title || title}]: ${cleanText.substring(0, 15000)}`;
                    } else {
                        throw new Error("Readability failed to extract content");
                    }
                } catch (e) {
                    console.warn("Readability failed, falling back to meta:", e);
                    const metaDesc = document.querySelector('meta[name="description"]')?.content;
                    contentToSave = `[Page Visit] Title: ${title}\nURL: ${url}\nSummary: ${metaDesc || "No description available."}`;
                }
            }

            // 2. Send to Background (Proxy to Local Server)
            return new Promise((resolve) => {
                if (typeof chrome === 'undefined' || !chrome.runtime || !chrome.runtime.sendMessage) {
                    resolve({ success: false, error: "Extension context missing or invalidated. Please reload the page." });
                    return;
                }

                try {
                    chrome.runtime.sendMessage({
                        action: "ingestGatekeeper",
                        payload: {
                            text: contentToSave,
                            context: null, // Let server find context
                            force_save: false, // Let Gatekeeper decide
                            source: "web_extension", // <--- NEW METADATA
                            source_url: url          // <--- NEW METADATA
                        }
                    }, (response) => {
                        if (chrome.runtime.lastError) {
                            resolve({ success: false, error: chrome.runtime.lastError.message });
                        } else {
                            resolve(response);
                        }
                    });
                } catch (e) {
                    resolve({ success: false, error: e.message });
                }
            });
        }
    }

    // --- 2. UI Component: Floating Action Button (FAB) ---
    class FabUI {
        constructor(onClickCallback) {
            this.onClick = onClickCallback;
            this.element = null;
            this._init();
        }

        _init() {
            if (document.getElementById('gemini-memory-fab')) return;

            this.element = document.createElement("div");
            this.element.id = "gemini-memory-fab";
            this.element.className = "fab-idle";
            this.element.innerText = "🧠";
            this.element.title = "Memorize this page";
            
            const style = document.createElement('style');
            style.textContent = `
                #gemini-memory-fab {
                    position: fixed;
                    bottom: 30px;
                    right: 30px;
                    width: 50px;
                    height: 50px;
                    border-radius: 50%;
                    background-color: #1a73e8;
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    cursor: pointer;
                    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                    z-index: 999999;
                    user-select: none;
                }
                #gemini-memory-fab:hover {
                    transform: scale(1.1);
                    background-color: #1557b0;
                }
                #gemini-memory-fab.fab-working {
                    background-color: #fbbc04;
                    animation: fab-spin 2s infinite linear;
                    pointer-events: none;
                }
                #gemini-memory-fab.fab-done {
                    background-color: #34a853;
                    transform: scale(1.2);
                }
                @keyframes fab-spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
            document.body.appendChild(this.element);

            this.element.addEventListener('click', () => this.onClick());
        }

        setState(state) {
            if (!this.element) return;
            this.element.classList.remove('fab-idle', 'fab-working', 'fab-done');
            
            switch (state) {
                case 'working':
                    this.element.classList.add('fab-working');
                    this.element.innerText = "⏳";
                    this.element.title = "Processing...";
                    break;
                case 'done':
                    this.element.classList.add('fab-done');
                    this.element.innerText = "✅";
                    this.element.title = "Memorized!";
                    // 2秒后自动回到 idle
                    setTimeout(() => this.setState('idle'), 2000);
                    break;
                case 'idle':
                default:
                    this.element.classList.add('fab-idle');
                    this.element.innerText = "🧠";
                    this.element.title = "Memorize this page";
                    break;
            }
        }
    }

    // --- 3. Controller ---
    class BrowserGatekeeperController {
        constructor() {
            this.fab = new FabUI(() => this.handleMemorize());
        }

        async handleMemorize() {
            this.fab.setState('working');
            
            try {
                // Use the Static Class Logic
                const result = await BrowserGatekeeper.memorize();
                
                if (result && result.success && result.data && result.data.action_result) {
                    this.fab.setState('done');
                    console.log("✅ Page Memorized:", result.data);
                } else {
                    this.fab.setState('idle');
                    const errMsg = (result && result.error) || (result && result.data ? result.data.detail : "Unknown error");
                    // alert("❌ Memorize failed: " + errMsg); // 暂时屏蔽 alert，避免干扰体验，只看 console
                    console.error("Memorize failed:", errMsg);
                }
            } catch (err) {
                this.fab.setState('idle');
                console.error("Memorize Exception:", err);
            }
        }
    }

    // --- 4. Bootstrap ---
    new BrowserGatekeeperController();

})();