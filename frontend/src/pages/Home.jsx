import { useEffect, useState } from 'react';
import { getNews } from '../api/client.js';
import CategoryNav from '../components/CategoryNav.jsx';
import SearchBar from '../components/SearchBar.jsx';
import ArticleCard from '../components/ArticleCard.jsx';
import { CardSkeleton } from '../components/Skeleton.jsx';

const CATEGORY_STORAGE_KEY = 'news:category';

function readStoredCategory() {
  try {
    return localStorage.getItem(CATEGORY_STORAGE_KEY) || '';
  } catch {
    return '';
  }
}

export default function Home() {
  // Navigating to /article/:id and back remounts Home (separate routes),
  // which would otherwise reset the category to "All" every time —
  // persist it so "back" returns to whatever was last selected.
  const [category, setCategory] = useState(readStoredCategory);
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

  function handleCategoryChange(next) {
    setCategory(next);
    try {
      localStorage.setItem(CATEGORY_STORAGE_KEY, next);
    } catch {
      /* private browsing / storage disabled — category just won't persist */
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <CategoryNav active={category} onChange={handleCategoryChange} />
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
        <div className="rounded-lg bg-destructive/10 p-5 text-sm text-destructive ring-1 ring-destructive/30">
          <p className="font-medium">Couldn't load the feed.</p>
          <p className="mt-1">{error.message}</p>
          <p className="mt-2 text-destructive/80">
            Make sure the server is running (npm run dev) and reachable.
          </p>
        </div>
      )}

      {!loading && !error && articles.length === 0 && (
        <div className="rounded-lg bg-card p-8 text-center text-sm text-muted-foreground ring-1 ring-border">
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
