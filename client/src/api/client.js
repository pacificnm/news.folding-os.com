const BASE = import.meta.env.VITE_API_URL || 'http://localhost:4000/api';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
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

export function getSummary(id) {
  return request(`/news/${encodeURIComponent(id)}/summarize`);
}

export function getResearch(id) {
  return request(`/news/${encodeURIComponent(id)}/research`);
}
