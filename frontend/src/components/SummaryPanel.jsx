import { useEffect, useState } from 'react';
import { streamSummary } from '../api/client.js';
import Spinner from './Spinner.jsx';

export default function SummaryPanel({ articleId }) {
  // Starts at 'loading', not 'idle': the effect below sets 'loading' too,
  // but only after the first render commits — an 'idle' initial state with
  // no corresponding render branch fell through to the ready-state return
  // (destructuring `state.data`) on that very first render, before the
  // fetch had even started, crashing with data still null every time.
  const [state, setState] = useState({ status: 'loading', data: null, error: null, streamText: '' });

  useEffect(() => {
    setState({ status: 'loading', data: null, error: null, streamText: '' });
    const source = streamSummary(articleId, {
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
          Summarizing…
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
          ? 'AI summaries are not configured. Set OLLAMA_BASE_URL on the server to enable this.'
          : `Could not load summary: ${state.error.message}`}
      </div>
    );
  }

  const { summary, keyPoints } = state.data;
  return (
    <div className="space-y-3">
      <p className="text-sm leading-relaxed text-foreground">{summary}</p>
      {keyPoints && keyPoints.length > 0 && (
        <ul className="space-y-1.5">
          {keyPoints.map((p, i) => (
            <li key={i} className="flex gap-2 text-sm text-foreground">
              <span className="mt-1.5 h-1.5 w-1.5 flex-none rounded-full bg-primary" />
              <span>{p}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
