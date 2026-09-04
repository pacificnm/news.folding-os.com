const CATEGORIES = ['All', 'World', 'US', 'Tech', 'Business', 'Science'];

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
                ? 'bg-brand-600 text-white'
                : 'bg-white text-slate-700 ring-1 ring-slate-200 hover:bg-slate-100')
            }
          >
            {c}
          </button>
        );
      })}
    </nav>
  );
}
