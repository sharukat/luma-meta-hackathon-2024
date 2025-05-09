// URL_Server/popup.js
document.addEventListener('DOMContentLoaded', async function() {
  // Get the current active tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  // Execute the content script
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ['contentScript.js']
  }, async (results) => {
    if (chrome.runtime.lastError) {
      console.error('Error:', chrome.runtime.lastError);
      return;
    }

    const data = results[0].result;
    displayUrls(data);
    
    // Send to server
    try {
      const response = await fetch('http://localhost:5000/process-links', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      console.log('Successfully sent to server');
    } catch (error) {
      console.error('Error sending to server:', error);
    }
  });
});

function displayUrls(data) {
  const container = document.getElementById('content');
  
  // Display current URL
  const currentUrlDiv = document.createElement('div');
  currentUrlDiv.innerHTML = `
    <h3>Current URL:</h3>
    <p class="current-url">${data.currentUrl}</p>
  `;
  container.appendChild(currentUrlDiv);
  
  // Display all URLs
  const urlsDiv = document.createElement('div');
  urlsDiv.innerHTML = `
    <h3>Found URLs (${data.allUrls.length}):</h3>
    <div class="url-list">
      ${data.allUrls.map(url => `
        <a href="${url}" target="_blank" class="url-item">${url}</a>
      `).join('')}
    </div>
  `;
  container.appendChild(urlsDiv);
}
