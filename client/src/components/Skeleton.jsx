export default function Skeleton({ className = '' }) {
  return <div className={`animate-pulse rounded-lg bg-slate-200 ${className}`} />;
}

export function CardSkeleton() {
  return (
    <div className="rounded-xl bg-white p-5 ring-1 ring-slate-200">
      <div className="mb-3 flex gap-2">
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-20" />
      </div>
      <Skeleton className="mb-2 h-5 w-full" />
      <Skeleton className="mb-2 h-5 w-4/5" />
      <Skeleton className="h-4 w-full" />
    </div>
  );
}
