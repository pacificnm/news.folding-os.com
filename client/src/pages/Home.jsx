import { useEffect, useState } from 'react';
import { getNews } from '../api/client.js';
import CategoryNav from '../components/CategoryNav.jsx';
import SearchBar from '../components/SearchBar.jsx';
import ArticleCard from '../components/ArticleCard.jsx';
import { CardSkeleton } from '../components/Skeleton.jsx';

export default function Home() {
  const [category, setCategory] = useState('');
  const [q, setQ] = useState('');
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getNews({ category, q, limit: 60 })
      .then((res) => {
        if (!cancelled) setArticles(res.articles || []);
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
  }, [category, q]);

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          news<span className="text-brand-600">.</span>folding-os.com
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          A multi-source news feed with AI summaries and research.
        </p>
      </header>

      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <CategoryNav active={category} onChange={setCategory} />
        <SearchBar onSearch={setQ} />
      </div>

      {loading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      )}

      {!loading && error && (
        <div className="rounded-lg bg-rose-50 p-5 text-sm text-rose-800 ring-1 ring-rose-200">
          <p className="font-medium">Couldn't load the feed.</p>
          <p className="mt-1">{error.message}</p>
          <p className="mt-2 text-rose-600">
            Make sure the server is running (npm run dev) and reachable.
          </p>
        </div>
      )}

      {!loading && !error && articles.length === 0 && (
        <div className="rounded-lg bg-white p-8 text-center text-sm text-slate-500 ring-1 ring-slate-200">
          No articles found. Try a different category or search term.
        </div>
      )}

      {!loading && !error && articles.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {articles.map((a) => (
            <ArticleCard key={a.id} article={a} />
          ))}
        </div>
      )}
    </div>
  );
}
