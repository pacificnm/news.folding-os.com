const BASE = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(body.message || `Request failed (${res.status})`);
    err.status = res.status;
    err.code = body.error;
    throw err;
  }
  return body;
}

export function getNews({ category, q, limit } = {}) {
  const params = new URLSearchParams();
  if (category) params.set('category', category);
  if (q) params.set('q', q);
  if (limit) params.set('limit', String(limit));
  const qs = params.toString();
  return request(`/news${qs ? `?${qs}` : ''}`);
}

export function getArticle(id) {
  return request(`/news/${encodeURIComponent(id)}`);
}

// Summarize/research stream as Server-Sent Events: "delta" ({text}) events
// while the model generates, then one "done" (the final shaped result) or
// "failed" ({error, message}) event. Returns the EventSource so callers can
// close it on unmount/article change.
function streamAi(path, { onDelta, onDone, onFailed, onConnectionError }) {
  const source = new EventSource(`${BASE}${path}`, { withCredentials: true });
  source.addEventListener('delta', (e) => onDelta(JSON.parse(e.data).text));
  source.addEventListener('done', (e) => {
    onDone(JSON.parse(e.data));
    source.close();
  });
  source.addEventListener('failed', (e) => {
    onFailed(JSON.parse(e.data));
    source.close();
  });
  source.onerror = () => {
    onConnectionError();
    source.close();
  };
  return source;
}

export function streamSummary(id, handlers) {
  return streamAi(`/news/${encodeURIComponent(id)}/summarize`, handlers);
}

export function streamResearch(id, handlers) {
  return streamAi(`/news/${encodeURIComponent(id)}/research`, handlers);
}
