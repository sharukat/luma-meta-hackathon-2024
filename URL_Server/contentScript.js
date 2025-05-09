// URL_Server/contentScript.js
function extractUrls() {
  // Get all links from the page
  const linkElements = document.querySelectorAll('a');
  const urls = Array.from(linkElements)
    .map(a => a.href)
    .filter(url => url && url.startsWith('http')); // Filter valid URLs only

  // Return both current URL and all found URLs
  return {
    currentUrl: window.location.href,
    allUrls: Array.from(new Set(urls)) // Remove duplicates
  };
}

extractUrls();

