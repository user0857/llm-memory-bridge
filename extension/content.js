/* content.js - DOM 操作核心 */

let cachedContext = "";
let lastQuery = "";
let debounceTimer = null;
let isPaused = false;
let isComposing = false;
let lastCompositionEndTime = 0;
let aiResponseDebounceTimer = null;
let lastSavedResponse = "";

// 1. 初始化状态并监听存储变化
chrome.storage.local.get(['isPaused'], (result) => {
  isPaused = !!result.isPaused;
  updateStatusIcon();
});

chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && changes.isPaused) {
    isPaused = changes.isPaused.newValue;
    updateStatusIcon();
    console.log("[Bridge] Pause state changed:", isPaused);
  }
});

// 创建状态指示灯 (网页右下角)
const statusIndicator = document.createElement("div");
statusIndicator.id = "gemini-memory-indicator";
statusIndicator.innerText = "M";
statusIndicator.title = "Memory Bridge (Click to open extension)";
document.body.appendChild(statusIndicator);

function updateStatusIcon(hasContext = false) {
  if (isPaused) {
    statusIndicator.style.backgroundColor = "#9e9e9e";
    statusIndicator.style.opacity = "0.6";
    statusIndicator.innerText = "M-";
  } else {
    statusIndicator.style.backgroundColor = hasContext ? "#4caf50" : "#ccc";
    statusIndicator.style.opacity = "1";
    statusIndicator.innerText = hasContext ? "M+" : "M";
  }
}

// 监听来自 Popup 的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getCurrentInput") {
    const inputArea = getInputArea();
    sendResponse({ text: inputArea ? inputArea.innerText : "" });
  }
});

// 辅助函数：查找输入框
function getInputArea() {
  let el = document.querySelector('div.rich-textarea > div[contenteditable="true"]');
  if (el) return el;
  const candidates = document.querySelectorAll('div[contenteditable="true"]');
  for (const c of candidates) {
      if (c.offsetParent !== null && c.clientHeight > 10) return c;
  }
  return document.querySelector('[role="textbox"]');
}

// 2. 核心搜索逻辑
function handleInput(e, delay = 2000) {
  // Debug Log: 让我们看看事件是否触发，以及状态如何
  // console.log(`[Bridge Debug] Input Event. Paused: ${isPaused}`);
  
  if (isPaused) return;
  
  const inputArea = getInputArea();
  if (!inputArea) {
      console.warn("[Bridge] Input area not found!");
      return;
  }
  
  const text = inputArea.innerText;
  if (!text || text.trim() === "") {
      updateStatusIcon(false);
      cachedContext = "";
      return;
  }

  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    if (text === lastQuery) return;
    lastQuery = text;
    
    chrome.runtime.sendMessage(
      { action: "searchContext", query: text },
      (response) => {
        if (response && response.success && response.data.source_count > 0) {
          cachedContext = response.data.context;
          updateStatusIcon(true);
        } else {
          cachedContext = "";
          updateStatusIcon(false);
        }
      }
    );
  }, delay);
}

function handlePaste(e) {
    if (isPaused) return;
    setTimeout(() => handleInput(null, 300), 50);
}

document.addEventListener('compositionstart', () => { isComposing = true; });
document.addEventListener('compositionend', () => {
    isComposing = false;
    lastCompositionEndTime = Date.now();
});

// 3. 拦截发送
function handleKeydown(e) {
  if (isPaused) return;
  const timeSinceComposition = Date.now() - lastCompositionEndTime;
  if (isComposing || timeSinceComposition < 100 || e.isComposing) return;

  if (e.key === "Enter" && !e.shiftKey) {
    const inputArea = getInputArea();
    if (!inputArea) return;

    const userText = inputArea.innerText;
    if (userText && userText.trim().length > 0) {
        chrome.runtime.sendMessage({ action: "addMemory", content: userText });
    }

    if (cachedContext) {
      const originalText = inputArea.innerText;
      if (!originalText.includes("【本地记忆库提示】")) {
           inputArea.innerText = originalText + "\n\n" + cachedContext;
           const inputEvent = new Event('input', { bubbles: true });
           inputArea.dispatchEvent(inputEvent);
      }
    }
  }
}

// 4. 监听 AI 回复
const responseObserver = new MutationObserver((mutations) => {
  if (isPaused) return;
  let hasNewText = false;
  for (const mutation of mutations) {
    if (mutation.addedNodes.length > 0 && mutation.target.nodeType === 1) {
        if (mutation.target.getAttribute('contenteditable') === 'true') continue;
        hasNewText = true;
    }
  }
  if (hasNewText) {
    clearTimeout(aiResponseDebounceTimer);
    aiResponseDebounceTimer = setTimeout(() => extractLastAIResponse(), 3000);
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
                md += `\n\n${node.innerText}\n\n`;
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
    if (isPaused) return;
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
    setInterval(() => {
        const inputArea = getInputArea();
        if (inputArea && !inputArea.dataset.bridgeAttached) {
            inputArea.addEventListener("input", (e) => handleInput(e, 2000));
            inputArea.addEventListener("paste", handlePaste);
            inputArea.addEventListener("keydown", handleKeydown, true); 
            inputArea.dataset.bridgeAttached = "true";
        }
    }, 1000); 
    responseObserver.observe(document.body, { childList: true, subtree: true, characterData: true });
}

if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", initBridge); } else { initBridge(); }
