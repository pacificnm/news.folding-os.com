export default function Skeleton({ className = '' }) {
  return <div className={`animate-pulse rounded-lg bg-muted ${className}`} />;
}

export function CardSkeleton() {
  return (
    <div className="rounded-xl bg-card p-5 ring-1 ring-border">
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
