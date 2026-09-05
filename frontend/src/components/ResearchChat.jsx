import { useEffect, useRef, useState } from 'react';
import { getChatHistory, streamChatMessage } from '../api/client.js';
import Spinner from './Spinner.jsx';

function ToolChip({ tool }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
      ⚙ {tool.name}
      {tool.ok === undefined ? ' …' : tool.ok ? ' ✓' : ' ✗'}
      {tool.duration_ms !== undefined ? ` · ${tool.duration_ms}ms` : ''}
    </span>
  );
}

function Bubble({ role, content, toolCalls }) {
  const isUser = role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed ${
          isUser
            ? 'bg-muted text-foreground'
            : 'bg-card text-foreground ring-1 ring-border'
        }`}
      >
        {toolCalls && toolCalls.length > 0 && (
          <div className="mb-1.5 flex flex-wrap gap-1.5">
            {toolCalls.map((t, i) => (
              <ToolChip key={i} tool={t} />
            ))}
          </div>
        )}
        <p className="whitespace-pre-wrap">{content}</p>
      </div>
    </div>
  );
}

export default function ResearchChat({ articleId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [liveText, setLiveText] = useState('');
  const [liveTools, setLiveTools] = useState([]);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    setMessages([]);
    setError(null);
    getChatHistory(articleId)
      .then((data) => {
        if (!cancelled) setMessages(data.messages || []);
      })
      .catch(() => {
        /* history is a nice-to-have; an empty thread is a fine fallback */
      });
    return () => {
      cancelled = true;
      abortRef.current?.abort();
    };
  }, [articleId]);

  async function send(e) {
    e.preventDefault();
    const message = input.trim();
    if (!message || sending) return;

    setMessages((m) => [...m, { role: 'user', content: message }]);
    setInput('');
    setSending(true);
    setError(null);
    setLiveText('');
    setLiveTools([]);

    const controller = new AbortController();
    abortRef.current = controller;

    let text = '';
    let tools = [];

    try {
      await streamChatMessage(articleId, message, (event, data) => {
        if (event === 'token') {
          text += data.text;
          setLiveText(text);
        } else if (event === 'tool_start') {
          tools = [...tools, { name: data.tool, index: data.index }];
          setLiveTools(tools);
        } else if (event === 'tool_end') {
          tools = tools.map((t) =>
            t.index === data.index ? { ...t, ok: data.ok, duration_ms: data.duration_ms } : t
          );
          setLiveTools(tools);
        } else if (event === 'done' || event === 'cancelled') {
          setMessages((m) => [...m, { role: 'assistant', content: data.text, toolCalls: tools }]);
          setLiveText('');
          setLiveTools([]);
        } else if (event === 'error') {
          setError(data.message || 'Something went wrong.');
        }
      }, controller.signal);
    } catch (err) {
      if (err.name !== 'AbortError') setError(err.message);
    } finally {
      setSending(false);
      abortRef.current = null;
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-3 overflow-y-auto">
        {messages.length === 0 && !sending && (
          <p className="text-sm text-muted-foreground">
            Ask a question about this article to start researching — the assistant can search
            the web for anything beyond what's here.
          </p>
        )}
        {messages.map((m, i) => (
          <Bubble key={i} role={m.role} content={m.content} toolCalls={m.toolCalls} />
        ))}
        {sending && (
          <Bubble
            role="assistant"
            content={liveText || '…'}
            toolCalls={liveTools}
          />
        )}
        {error && (
          <div className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive ring-1 ring-destructive/30">
            {error}
          </div>
        )}
      </div>

      <form onSubmit={send} className="mt-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about this article…"
          aria-label="Research chat message"
          disabled={sending}
          className="flex-1 rounded-lg border border-input bg-card px-3 py-2 text-sm text-foreground outline-none focus:border-ring focus:ring-2 focus:ring-ring/30 disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {sending && <Spinner />}
          Send
        </button>
      </form>
    </div>
  );
}
