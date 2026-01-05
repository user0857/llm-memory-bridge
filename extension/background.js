// background.js - 负责跨域通信
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "updateIcon") {
      // 使用下载好的 PNG 图标
      let iconPath = "icons/icon-gray.png";
      if (request.status === "active") iconPath = "icons/icon-green.png";
      if (request.status === "error") iconPath = "icons/icon-red.png";
      
      // 清除可能残留的 Badge
      chrome.action.setBadgeText({ text: "" });
      
      // 明确指定 tabId，确保只更新当前标签页的图标
      const options = { path: iconPath };
      if (sender.tab && sender.tab.id) {
          options.tabId = sender.tab.id;
      }
      
      chrome.action.setIcon(options);
      return false;
  }
  
  if (request.action === "searchContext") {
    fetch("http://127.0.0.1:8000/search_context", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_input: request.query })
    })
    .then(response => response.json())
    .then(data => sendResponse({ success: true, data: data }))
    .catch(error => {
      console.error("Bridge Error:", error);
      sendResponse({ success: false, error: error.message });
    });
    return true; // 保持消息通道开放以进行异步响应
  }
  
  if (request.action === "addMemory") {
      fetch("http://127.0.0.1:8000/add_memory", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: request.content, tags: ["web-chat"] })
    })
    .then(response => response.json())
    .then(data => sendResponse({ success: true, data: data }))
    .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
});
