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

export function getChatHistory(id) {
  return request(`/news/${encodeURIComponent(id)}/chat`);
}

// Research-chat turn as SSE, same event shape as agent.py's run_turn:
// token/tool_start/tool_output/tool_end/done/cancelled/error. POSTs a body,
// so EventSource (GET-only) can't be used — hand-parse frames from a
// fetch() stream instead (ported from chat.folding-os.com's lib/api.ts).
export async function streamChatMessage(id, message, onEvent, signal) {
  const res = await fetch(`${BASE}/news/${encodeURIComponent(id)}/chat`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
    signal,
  });
  if (!res.ok || !res.body) {
    const body = await res.json().catch(() => ({}));
    const err = new Error(body.message || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = '';
  let event = 'message';
  const dataLines = [];

  const dispatch = () => {
    if (dataLines.length === 0) {
      event = 'message';
      return;
    }
    const raw = dataLines.join('\n');
    dataLines.length = 0;
    let data = {};
    try {
      data = JSON.parse(raw);
    } catch {
      data = { text: raw };
    }
    onEvent(event, data);
    event = 'message';
  };

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let nl;
    while ((nl = buf.indexOf('\n')) >= 0) {
      const line = buf.slice(0, nl).replace(/\r$/, '');
      buf = buf.slice(nl + 1);
      if (line === '') {
        dispatch();
      } else if (line.startsWith('event:')) {
        event = line.slice(6).trim();
      } else if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).trimStart());
      }
    }
  }
  dispatch();
}
