import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

export default function EmptyState({
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="c2-card flex min-h-40 flex-col items-center justify-center gap-2 p-6 text-center">
      <h2 className="text-base font-semibold text-text-primary">{title}</h2>
      {description && (
        <p className="max-w-md text-sm text-text-secondary">{description}</p>
      )}
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}
