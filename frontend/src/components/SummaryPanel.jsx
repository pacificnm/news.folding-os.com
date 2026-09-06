import { useEffect, useRef, useState } from 'react';
import { streamSummary } from '../api/client.js';
import Spinner from './Spinner.jsx';

export default function SummaryPanel({ articleId }) {
  // Starts idle: summarizing costs a real model call, so it only runs when
  // the user actually asks for it (the Launch button below), not on every
  // article view.
  const [state, setState] = useState({ status: 'idle', data: null, error: null, streamText: '' });
  const sourceRef = useRef(null);

  useEffect(() => {
    setState({ status: 'idle', data: null, error: null, streamText: '' });
    return () => sourceRef.current?.close();
  }, [articleId]);

  function launch() {
    setState({ status: 'loading', data: null, error: null, streamText: '' });
    sourceRef.current = streamSummary(articleId, {
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
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-foreground">AI Summary</h2>
        {(state.status === 'idle' || state.status === 'error') && (
          <button
            type="button"
            onClick={launch}
            className="rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            {state.status === 'error' ? 'Try again' : 'Launch'}
          </button>
        )}
      </div>

      {state.status === 'idle' && (
        <p className="text-sm text-muted-foreground">Click Launch to generate an AI summary.</p>
      )}

      {state.status === 'loading' && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Spinner />
            Summarizing…
          </div>
          {state.streamText && (
            <p className="text-sm leading-relaxed text-foreground/70">{state.streamText}</p>
          )}
        </div>
      )}

      {state.status === 'error' &&
        (() => {
          const notConfigured = state.error && state.error.error === 'AI_NOT_CONFIGURED';
          return (
            <div className="rounded-lg bg-amber-500/10 p-4 text-sm text-amber-400 ring-1 ring-amber-500/30">
              {notConfigured
                ? 'AI summaries are not configured. Set OLLAMA_BASE_URL on the server to enable this.'
                : `Could not load summary: ${state.error.message}`}
            </div>
          );
        })()}

      {state.status === 'ready' && (
        <div className="space-y-3">
          <p className="text-sm leading-relaxed text-foreground">{state.data.summary}</p>
          {state.data.keyPoints && state.data.keyPoints.length > 0 && (
            <ul className="space-y-1.5">
              {state.data.keyPoints.map((p, i) => (
                <li key={i} className="flex gap-2 text-sm text-foreground">
                  <span className="mt-1.5 h-1.5 w-1.5 flex-none rounded-full bg-primary" />
                  <span>{p}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
