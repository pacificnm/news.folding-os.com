import { useEffect, useState } from 'react';
import { streamResearch } from '../api/client.js';
import Spinner from './Spinner.jsx';

function Section({ title, children }) {
  return (
    <div>
      <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h4>
      {children}
    </div>
  );
}

export default function ResearchPanel({ articleId }) {
  // Starts at 'loading', not 'idle': the effect below sets 'loading' too,
  // but only after the first render commits — an 'idle' initial state with
  // no corresponding render branch fell through to the ready-state return
  // (destructuring `state.data`) on that very first render, before the
  // fetch had even started, crashing with data still null every time.
  const [state, setState] = useState({ status: 'loading', data: null, error: null, streamText: '' });

  useEffect(() => {
    setState({ status: 'loading', data: null, error: null, streamText: '' });
    const source = streamResearch(articleId, {
      onDelta: (text) => setState((s) => ({ ...s, streamText: s.streamText + text })),
      onDone: (data) => setState({ status: 'ready', data, error: null, streamText: '' }),
      onFailed: (error) => setState({ status: 'error', data: null, error, streamText: '' }),
      onConnectionError: () =>
        setState((s) =>
          s.status === 'loading'
            ? { status: 'error', data: null, error: { message: 'Connection lost' }, streamText: '' }
            : s
        ),
    });
    return () => source.close();
  }, [articleId]);

  if (state.status === 'loading') {
    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Spinner />
          Researching…
        </div>
        {state.streamText && (
          <p className="text-sm leading-relaxed text-foreground/70">{state.streamText}</p>
        )}
      </div>
    );
  }

  if (state.status === 'error') {
    const notConfigured = state.error && state.error.error === 'AI_NOT_CONFIGURED';
    return (
      <div className="rounded-lg bg-amber-500/10 p-4 text-sm text-amber-400 ring-1 ring-amber-500/30">
        {notConfigured
          ? 'AI research is not configured. Set OLLAMA_BASE_URL on the server to enable this.'
          : `Could not load research: ${state.error.message}`}
      </div>
    );
  }

  const d = state.data;
  return (
    <div className="space-y-4">
      {d.context && (
        <Section title="Context">
          <p className="text-sm leading-relaxed text-foreground">{d.context}</p>
        </Section>
      )}

      {d.entities && d.entities.length > 0 && (
        <Section title="Entities">
          <div className="flex flex-wrap gap-2">
            {d.entities.map((e, i) => (
              <span
                key={i}
                className="rounded-full bg-muted px-3 py-1 text-xs text-foreground"
              >
                {e.name || JSON.stringify(e)}
                {e.type ? <span className="ml-1 text-muted-foreground">({e.type})</span> : null}
              </span>
            ))}
          </div>
        </Section>
      )}

      {d.claims && d.claims.length > 0 && (
        <Section title="Key claims">
          <ul className="space-y-1.5">
            {d.claims.map((c, i) => (
              <li key={i} className="flex gap-2 text-sm text-foreground">
                <span className="mt-1.5 h-1.5 w-1.5 flex-none rounded-full bg-primary" />
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
                className="rounded-full bg-accent px-3 py-1 text-xs font-medium text-accent-foreground"
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
              <li key={i} className="flex gap-2 text-sm text-foreground">
                <span className="text-primary">?</span>
                <span>{q}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}
