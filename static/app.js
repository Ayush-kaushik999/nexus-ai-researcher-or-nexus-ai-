const queryInput = document.querySelector('#queryInput');
const submitButton = document.querySelector('#submitBtn');
const privacyToggle = document.querySelector('#privacyToggle');
const searchToggle = document.querySelector('#searchToggle');
const providerSelect = document.querySelector('#providerSelect');
const privacyNote = document.querySelector('#privacyNote');
const charCount = document.querySelector('#charCount');
const loader = document.querySelector('#loader');
const loaderText = document.querySelector('#loaderText');
const outputPanel = document.querySelector('#outputPanel');
const errorPanel = document.querySelector('#errorPanel');

function syncSettings() {
  const privateMode = privacyToggle.checked;
  searchToggle.disabled = privateMode;
  providerSelect.disabled = privateMode;
  if (privateMode) {
    searchToggle.checked = false;
    providerSelect.value = 'ollama';
    privacyNote.textContent = 'Private mode uses local Ollama and disables web tools.';
  } else if (providerSelect.value === 'ollama') {
    privacyNote.textContent = 'Ollama runs locally; web research still contacts external search services.';
  } else {
    privacyNote.textContent = 'Groq sends your request to its cloud API.';
  }
}

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  loader.hidden = !isLoading;
  if (isLoading) {
    loaderText.textContent = searchToggle.checked ? 'Searching and analyzing...' : 'Thinking locally...';
  }
}

function escapeHtml(value) {
  return value.replace(/[&<>'"]/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[character]));
}

function renderDetails(value) {
  return escapeHtml(value)
    .split(/\r?\n/)
    .map(line => {
      if (line.startsWith('### ')) return `<h4>${line.slice(4)}</h4>`;
      if (line.startsWith('## ')) return `<h3>${line.slice(3)}</h3>`;
      if (line.startsWith('# ')) return `<h2>${line.slice(2)}</h2>`;
      if (line.startsWith('* ')) return `<li>${line.slice(2)}</li>`;
      return line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    })
    .join('<br>');
}

async function submitQuery() {
  const query = queryInput.value.trim();
  if (!query) {
    queryInput.focus();
    return;
  }
  setLoading(true);
  outputPanel.hidden = true;
  errorPanel.hidden = true;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 180000);
  try {
    const response = await fetch('/api/research', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
      body: JSON.stringify({
        query,
        privacy_mode: privacyToggle.checked,
        use_web_search: searchToggle.checked,
        provider: providerSelect.value
      })
    });
    const contentType = response.headers.get('content-type') || '';
    const data = contentType.includes('application/json')
      ? await response.json()
      : {};
    if (!response.ok) throw new Error(data.detail || `Request failed (${response.status}).`);
    document.querySelector('#summaryContent').textContent = data.summary;
    document.querySelector('#detailsContent').innerHTML = renderDetails(data.details || '');
    document.querySelector('#toolsBadge').textContent = (data.tools_used || []).join(' · ');
    const facts = document.querySelector('#keyFactsList');
    const keyFacts = Array.isArray(data.key_facts) ? data.key_facts : [];
    facts.replaceChildren(...keyFacts.map(fact => {
      const item = document.createElement('li'); item.textContent = fact; return item;
    }));
    document.querySelector('#keyFactsCard').hidden = keyFacts.length === 0;
    outputPanel.hidden = false;
  } catch (error) {
    errorPanel.textContent = error.name === 'AbortError'
      ? 'The request timed out. Ollama may still be loading the model; try again.'
      : error.message;
    errorPanel.hidden = false;
  } finally {
    clearTimeout(timeoutId);
    setLoading(false);
  }
}

privacyToggle.addEventListener('change', syncSettings);
providerSelect.addEventListener('change', syncSettings);
queryInput.addEventListener('input', () => { charCount.textContent = `${queryInput.value.length} / 1000`; });
queryInput.addEventListener('keydown', event => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') submitQuery();
});
submitButton.addEventListener('click', submitQuery);
syncSettings();