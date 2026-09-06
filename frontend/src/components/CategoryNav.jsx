const CATEGORIES = ['All', 'World', 'US', 'Local', 'Tech', 'Business', 'Science'];

export default function CategoryNav({ active, onChange }) {
  return (
    <nav className="flex flex-wrap gap-2" aria-label="Categories">
      {CATEGORIES.map((c) => {
        const value = c === 'All' ? '' : c;
        const isActive = (active || '') === value;
        return (
          <button
            key={c}
            type="button"
            onClick={() => onChange(value)}
            className={
              'rounded-full px-4 py-1.5 text-sm font-medium transition-colors ' +
              (isActive
                ? 'bg-primary text-primary-foreground'
                : 'bg-card text-foreground ring-1 ring-border hover:bg-muted')
            }
          >
            {c}
          </button>
        );
      })}
    </nav>
  );
}
