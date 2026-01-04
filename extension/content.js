/* content.js - DOM 操作核心 */

let cachedContext = "";
let lastQuery = "";
let debounceTimer = null;

// 创建状态指示灯
const statusIndicator = document.createElement("div");
statusIndicator.id = "gemini-memory-indicator";
statusIndicator.innerText = "M";
statusIndicator.title = "Memory Bridge Active";
document.body.appendChild(statusIndicator);

function updateStatus(active) {
  statusIndicator.style.backgroundColor = active ? "#4caf50" : "#ccc";
  statusIndicator.style.opacity = active ? "1" : "0.5";
  if (active) statusIndicator.innerText = "M+"; // 表示有记忆注入
  else statusIndicator.innerText = "M";
}

// 查找输入框 (Gemini 的输入框通常是一个 contenteditable 的 div)
function getInputArea() {
  let el = document.querySelector('div.rich-textarea > div[contenteditable="true"]');
  if (el) return el;

  const candidates = document.querySelectorAll('div[contenteditable="true"]');
  for (const c of candidates) {
      if (c.offsetParent !== null && c.clientHeight > 10) {
          return c;
      }
  }
  
  el = document.querySelector('[role="textbox"]');
  if (el) return el;

  return null;
}

function getSendButton() {
    return document.querySelector('button[aria-label*="Send"]') || 
           document.querySelector('button[class*="send-button"]');
}

// 1. 核心搜索逻辑
function handleInput(e, delay = 2000) {
  // 兼容事件对象和直接传入的字符串
  const inputArea = getInputArea();
  if (!inputArea) return;
  
  const text = inputArea.innerText;
  if (!text || text.trim() === "") {
      updateStatus(false);
      cachedContext = "";
      return;
  }

  // 使用自定义或默认延迟进行防抖
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    if (text === lastQuery) return;
    lastQuery = text;
    
    console.log("[Bridge] Searching context for:", text);
    chrome.runtime.sendMessage(
      { action: "searchContext", query: text },
      (response) => {
        if (response && response.success && response.data.source_count > 0) {
          cachedContext = response.data.context;
          console.log("[Bridge] Found context:", cachedContext);
          updateStatus(true);
        } else {
          cachedContext = "";
          updateStatus(false);
        }
      }
    );
  }, delay);
}

// 监听粘贴事件
function handlePaste(e) {
    console.log("[Bridge] Paste detected, triggering quick search.");
    // 粘贴后稍微等 DOM 更新再抓取文本
    setTimeout(() => {
        handleInput(null, 300); // 粘贴后 300ms 立即搜索
    }, 50);
}

// 全局变量追踪输入法状态
let isComposing = false;
let lastCompositionEndTime = 0;

document.addEventListener('compositionstart', () => { isComposing = true; });
document.addEventListener('compositionend', () => {
    isComposing = false;
    lastCompositionEndTime = Date.now();
});

// 2. 拦截发送
function handleKeydown(e) {
  const timeSinceComposition = Date.now() - lastCompositionEndTime;
  if (isComposing || timeSinceComposition < 100 || e.isComposing) {
      return;
  }

  if (e.key === "Enter" && !e.shiftKey) {
    const inputArea = getInputArea();
    if (!inputArea) return;

    const userText = inputArea.innerText;
    if (userText && userText.trim().length > 0) {
        console.log("[Bridge] Capturing memory:", userText);
        chrome.runtime.sendMessage({
            action: "addMemory", 
            content: userText 
        });
    }

    if (cachedContext) {
      const originalText = inputArea.innerText;
      if (!originalText.includes("【本地记忆库提示】")) {
           inputArea.innerText = originalText + "\n\n" + cachedContext;
           const inputEvent = new Event('input', { bubbles: true });
           inputArea.dispatchEvent(inputEvent);
           console.log("[Bridge] Context injected just before send.");
      }
    }
  }
}

// 3. 监听 AI 回复
let aiResponseDebounceTimer = null;
let lastSavedResponse = "";

const responseObserver = new MutationObserver((mutations) => {
  let hasNewText = false;
  for (const mutation of mutations) {
    if (mutation.addedNodes.length > 0 && mutation.target.nodeType === 1) {
        if (mutation.target.getAttribute('contenteditable') === 'true') continue;
        hasNewText = true;
    }
  }
  if (hasNewText) {
    clearTimeout(aiResponseDebounceTimer);
    aiResponseDebounceTimer = setTimeout(() => {
      extractLastAIResponse();
    }, 3000);
  }
});

function domToMarkdown(element) {
    let md = "";
    for (const node of element.childNodes) {
        if (node.nodeType === Node.TEXT_NODE) {
            md += node.textContent;
        } else if (node.nodeType === Node.ELEMENT_NODE) {
            const tagName = node.tagName.toLowerCase();
            if (tagName === 'pre' || node.classList.contains('code-block')) {
                md += `\n\
\n${node.innerText}\n\
\
`;
            } else if (tagName === 'img') {
                if (node.src && !node.src.startsWith('data:')) {
                     md += `\n![${node.alt || 'Image'}](${node.src})\n`;
                }
            } else if (tagName === 'p') {
                md += domToMarkdown(node) + "\n\n";
            } else if (tagName === 'li') {
                md += "- " + domToMarkdown(node) + "\n";
            } else {
                md += domToMarkdown(node);
            }
        }
    }
    return md;
}

function extractLastAIResponse() {
    const potentialContainers = document.querySelectorAll('.model-response-text, [data-test-id="model-response-text"]');
    let targetContainer = null;
    if (potentialContainers.length > 0) {
        targetContainer = potentialContainers[potentialContainers.length - 1];
    } else {
        const paragraphs = document.querySelectorAll('p');
        for (let i = paragraphs.length - 1; i >= 0; i--) {
             if (!paragraphs[i].closest('[contenteditable="true"]')) {
                 targetContainer = paragraphs[i].closest('div'); 
                 if (targetContainer && targetContainer.innerText.length > 50) break;
             }
        }
    }
    if (targetContainer) {
        const markdownText = domToMarkdown(targetContainer).trim();
        if (markdownText && markdownText !== lastSavedResponse && markdownText.length > 20) {
            lastSavedResponse = markdownText;
            chrome.runtime.sendMessage({ action: "addMemory", content: "Gemini: " + markdownText });
        }
    }
}

function initBridge() {
    console.log("[Bridge] Initializing...");
    setInterval(() => {
        const inputArea = getInputArea();
        if (inputArea && !inputArea.dataset.bridgeAttached) {
            console.log("[Bridge] Input area found via polling, attaching listeners.");
            inputArea.addEventListener("input", (e) => handleInput(e, 2000));
            inputArea.addEventListener("paste", handlePaste);
            inputArea.addEventListener("keydown", handleKeydown, true); 
            inputArea.dataset.bridgeAttached = "true";
        }
    }, 1000); 
    responseObserver.observe(document.body, { childList: true, subtree: true, characterData: true });
}

if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", initBridge); } else { initBridge(); }