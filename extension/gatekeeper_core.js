/**
 * Browser Gatekeeper Core
 * 负责在前端提取、清洗、脱敏网页内容
 */

const BrowserGatekeeper = {
    // 1. 提取核心内容
    extract: function() {
        console.log("🧠 Browser Gatekeeper is scanning the page...");
        
        // ... (省略部分保持不变)
        const selectors = ['article', 'main', '.post-content', '#content', '.article-body'];
        let mainElement = null;
        for (const selector of selectors) {
            mainElement = document.querySelector(selector);
            if (mainElement) break;
        }
        
        const root = mainElement || document.body;
        const clone = root.cloneNode(true);
        
        const noise = ['nav', 'footer', 'header', 'script', 'style', 'noscript', 'iframe', 'svg', '.ads', '.sidebar', '.menu'];
        noise.forEach(s => {
            clone.querySelectorAll(s).forEach(el => el.remove());
        });
        
        const title = document.title;
        const url = window.location.href;
        const text = clone.innerText.replace(/\s+/g, ' ').trim();
        
        return {
            title: title,
            url: url,
            content: text.slice(0, 5000)
        };
    },

    // 2. 发送到后端 Proxy (Gatekeeper) via Background Script
    memorize: async function() {
        const data = this.extract();
        // 不再直接 fetch，而是发消息给 background.js
        return new Promise((resolve) => {
            chrome.runtime.sendMessage({
                action: "ingestGatekeeper",
                url: "http://127.0.0.1:8000/api/gatekeeper/ingest", // URL 其实可以在 background 里硬编码，但这里传过去也行
                payload: {
                    text: data.content,
                    context: `Source URL: ${data.url}\nPage Title: ${data.title}`,
                    force_save: false
                }
            }, (response) => {
                if (response && response.success) {
                    resolve({ success: true, detail: response.data.action_result, decision: response.data.decision });
                } else {
                    console.error("❌ Gatekeeper Sync Failed:", response ? response.error : "Unknown error");
                    resolve({ success: false, error: response ? response.error : "Communication failed" });
                }
            });
        });
    }
};
