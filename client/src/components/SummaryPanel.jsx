import { useEffect, useState } from 'react';
import { getSummary } from '../api/client.js';

export default function SummaryPanel({ articleId }) {
  const [state, setState] = useState({ status: 'idle', data: null, error: null });

  useEffect(() => {
    let cancelled = false;
    setState({ status: 'loading', data: null, error: null });
    getSummary(articleId)
      .then((data) => {
        if (!cancelled) setState({ status: 'ready', data, error: null });
      })
      .catch((err) => {
        if (!cancelled) setState({ status: 'error', data: null, error: err });
      });
    return () => {
      cancelled = true;
    };
  }, [articleId]);

  if (state.status === 'loading') {
    return (
      <div className="space-y-2">
        <div className="h-4 w-full animate-pulse rounded bg-slate-200" />
        <div className="h-4 w-5/6 animate-pulse rounded bg-slate-200" />
        <div className="h-4 w-4/6 animate-pulse rounded bg-slate-200" />
      </div>
    );
  }

  if (state.status === 'error') {
    const notConfigured = state.error && state.error.code === 'AI_NOT_CONFIGURED';
    return (
      <div className="rounded-lg bg-amber-50 p-4 text-sm text-amber-800 ring-1 ring-amber-200">
        {notConfigured
          ? 'AI summaries are not configured. Set OPENAI_API_KEY on the server to enable this.'
          : `Could not load summary: ${state.error.message}`}
      </div>
    );
  }

  const { summary, keyPoints } = state.data;
  return (
    <div className="space-y-3">
      <p className="text-sm leading-relaxed text-slate-700">{summary}</p>
      {keyPoints && keyPoints.length > 0 && (
        <ul className="space-y-1.5">
          {keyPoints.map((p, i) => (
            <li key={i} className="flex gap-2 text-sm text-slate-700">
              <span className="mt-1.5 h-1.5 w-1.5 flex-none rounded-full bg-brand-500" />
              <span>{p}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
