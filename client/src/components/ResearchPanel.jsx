import { useEffect, useState } from 'react';
import { getResearch } from '../api/client.js';

function Section({ title, children }) {
  return (
    <div>
      <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
        {title}
      </h4>
      {children}
    </div>
  );
}

export default function ResearchPanel({ articleId }) {
  const [state, setState] = useState({ status: 'idle', data: null, error: null });

  useEffect(() => {
    let cancelled = false;
    setState({ status: 'loading', data: null, error: null });
    getResearch(articleId)
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
        <div className="h-4 w-2/3 animate-pulse rounded bg-slate-200" />
      </div>
    );
  }

  if (state.status === 'error') {
    const notConfigured = state.error && state.error.code === 'AI_NOT_CONFIGURED';
    return (
      <div className="rounded-lg bg-amber-50 p-4 text-sm text-amber-800 ring-1 ring-amber-200">
        {notConfigured
          ? 'AI research is not configured. Set OPENAI_API_KEY on the server to enable this.'
          : `Could not load research: ${state.error.message}`}
      </div>
    );
  }

  const d = state.data;
  return (
    <div className="space-y-4">
      {d.context && (
        <Section title="Context">
          <p className="text-sm leading-relaxed text-slate-700">{d.context}</p>
        </Section>
      )}

      {d.entities && d.entities.length > 0 && (
        <Section title="Entities">
          <div className="flex flex-wrap gap-2">
            {d.entities.map((e, i) => (
              <span
                key={i}
                className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700"
              >
                {e.name || JSON.stringify(e)}
                {e.type ? <span className="ml-1 text-slate-400">({e.type})</span> : null}
              </span>
            ))}
          </div>
        </Section>
      )}

      {d.claims && d.claims.length > 0 && (
        <Section title="Key claims">
          <ul className="space-y-1.5">
            {d.claims.map((c, i) => (
              <li key={i} className="flex gap-2 text-sm text-slate-700">
                <span className="mt-1.5 h-1.5 w-1.5 flex-none rounded-full bg-brand-500" />
                <span>{c}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {d.relatedTopics && d.relatedTopics.length > 0 && (
        <Section title="Related topics">
          <div className="flex flex-wrap gap-2">
            {d.relatedTopics.map((t, i) => (
              <span
                key={i}
                className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700"
              >
                {t}
              </span>
            ))}
          </div>
        </Section>
      )}

      {d.openQuestions && d.openQuestions.length > 0 && (
        <Section title="Open questions">
          <ul className="space-y-1.5">
            {d.openQuestions.map((q, i) => (
              <li key={i} className="flex gap-2 text-sm text-slate-700">
                <span className="text-brand-500">?</span>
                <span>{q}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}
