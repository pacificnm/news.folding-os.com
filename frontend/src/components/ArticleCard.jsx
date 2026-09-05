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
      className="group flex flex-col overflow-hidden rounded-xl bg-card ring-1 ring-border transition-shadow hover:shadow-md hover:shadow-black/20"
    >
      {article.imageUrl && (
        <img
          src={article.imageUrl}
          alt=""
          loading="lazy"
          onError={(e) => {
            e.currentTarget.style.display = 'none';
          }}
          className="h-40 w-full object-cover"
        />
      )}
      <div className="flex flex-1 flex-col p-5">
        <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
          <span className="rounded-full bg-accent px-2 py-0.5 font-medium text-accent-foreground">
            {article.category}
          </span>
          <span>{article.source}</span>
          <span aria-hidden>·</span>
          <span>{timeAgo(article.publishedAt)}</span>
        </div>
        <h3 className="text-base font-semibold leading-snug text-foreground group-hover:text-primary">
          {article.title}
        </h3>
        {article.description && (
          <p className="mt-2 line-clamp-3 text-sm text-muted-foreground">{article.description}</p>
        )}
      </div>
    </Link>
  );
}
