import { Link } from 'react-router-dom';

function timeAgo(iso) {
  if (!iso) return '';
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return '';
  const secs = Math.floor((Date.now() - then) / 1000);
  if (secs < 60) return 'just now';
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export default function ArticleCard({ article }) {
  return (
    <Link
      to={`/article/${encodeURIComponent(article.id)}`}
      className="group flex flex-col rounded-xl bg-white p-5 ring-1 ring-slate-200 transition-shadow hover:shadow-md"
    >
      <div className="mb-2 flex items-center gap-2 text-xs text-slate-500">
        <span className="rounded-full bg-brand-50 px-2 py-0.5 font-medium text-brand-700">
          {article.category}
        </span>
        <span>{article.source}</span>
        <span aria-hidden>·</span>
        <span>{timeAgo(article.publishedAt)}</span>
      </div>
      <h3 className="text-base font-semibold leading-snug text-slate-900 group-hover:text-brand-700">
        {article.title}
      </h3>
      {article.description && (
        <p className="mt-2 line-clamp-3 text-sm text-slate-600">{article.description}</p>
      )}
    </Link>
  );
}
