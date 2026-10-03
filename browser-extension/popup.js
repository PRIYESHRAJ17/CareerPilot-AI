async function activeTab() {
  const tabs = await chrome.tabs.query({active: true, currentWindow: true});
  return tabs[0];
}

async function loadPage(tab) {
  if (!tab?.id) return {};
  try {
    return await chrome.scripting.executeScript({target: {tabId: tab.id}, func: () => ({
      title: document.title,
      url: window.location.href,
      description: document.querySelector('meta[name="description"]')?.getAttribute('content') || '',
      company: document.querySelector('[class*="company" i]')?.textContent?.trim()?.slice(0, 300) || '',
      location: document.querySelector('[class*="location" i]')?.textContent?.trim()?.slice(0, 300) || ''
    })}).then(result => result?.[0]?.result || {}).catch(() => ({}));
  } catch { return {}; }
}

(async () => {
  const tab = await activeTab();
  const page = await loadPage(tab);
  document.querySelector('#title').value = page.title || '';
  document.querySelector('#company').value = page.company || '';
  document.querySelector('#location').value = page.location || '';
  const saved = await chrome.storage.local.get(['api', 'token']);
  if (saved.api) document.querySelector('#api').value = saved.api;
  if (saved.token) document.querySelector('#token').value = saved.token;

  document.querySelector('#save').addEventListener('click', async () => {
    const api = document.querySelector('#api').value.trim().replace(/\/$/, '');
    const token = document.querySelector('#token').value.trim();
    const body = {
      url: page.url || tab?.url || '',
      title: document.querySelector('#title').value.trim() || 'Captured opportunity',
      company: document.querySelector('#company').value.trim(),
      location: document.querySelector('#location').value.trim(),
      notes: document.querySelector('#notes').value.trim(),
      description: page.description || ''
    };
    const status = document.querySelector('#status');
    try {
      await chrome.storage.local.set({api, token});
      const response = await fetch(`${api}/integrations/clipper/jobs`, {
        method: 'POST', headers: {'Content-Type': 'application/json', 'X-CareerPilot-Clipper-Token': token}, body: JSON.stringify(body)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
      status.textContent = 'Saved to CareerPilot ✓';
    } catch (error) { status.textContent = `Save failed: ${error.message}`; }
  });
})();
