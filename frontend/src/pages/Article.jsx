import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getArticle } from '../api/client.js';
import SummaryPanel from '../components/SummaryPanel.jsx';
import ResearchChat from '../components/ResearchChat.jsx';
import { CardSkeleton } from '../components/Skeleton.jsx';

export default function Article() {
  const { id } = useParams();
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getArticle(id)
      .then((a) => {
        if (!cancelled) setArticle(a);
      })
      .catch((err) => {
        if (!cancelled) setError(err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <CardSkeleton />
      </div>
    );
  }

  if (error || !article) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <div className="rounded-lg bg-destructive/10 p-5 text-sm text-destructive ring-1 ring-destructive/30">
          <p className="font-medium">Article not found.</p>
          <p className="mt-1">{error ? error.message : 'It may have expired from the feed.'}</p>
          <Link to="/" className="mt-3 inline-block font-medium text-primary hover:underline">
            ← Back to feed
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <Link to="/" className="mb-4 inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline">
        ← Back to feed
      </Link>

      <article className="rounded-xl bg-card p-6 ring-1 ring-border">
        <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span className="rounded-full bg-accent px-2 py-0.5 font-medium text-accent-foreground">
            {article.category}
          </span>
          <span>{article.source}</span>
          {article.publishedAt && <span>· {new Date(article.publishedAt).toLocaleString()}</span>}
        </div>
        <h1 className="text-2xl font-bold leading-tight text-foreground">{article.title}</h1>
        {article.description && (
          <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{article.description}</p>
        )}
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 inline-flex items-center gap-1 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Read original ↗
        </a>
      </article>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="rounded-xl bg-card p-6 ring-1 ring-border">
          <h2 className="mb-3 text-lg font-semibold text-foreground">AI Summary</h2>
          <SummaryPanel articleId={article.id} />
        </section>

        <section className="flex min-h-[28rem] flex-col rounded-xl bg-card p-6 ring-1 ring-border">
          <h2 className="mb-3 text-lg font-semibold text-foreground">Research Chat</h2>
          <ResearchChat articleId={article.id} />
        </section>
      </div>
    </div>
  );
}
