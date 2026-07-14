interface LoadingProps {
  label?: string;
  className?: string;
}

export default function Loading({
  label = "Loading",
  className = "",
}: LoadingProps) {
  return (
    <div
      className={`flex items-center justify-center gap-3 py-10 text-sm text-text-secondary ${className}`}
      role="status"
      aria-live="polite"
    >
      <span
        aria-hidden="true"
        className="size-4 animate-spin rounded-full border-2 border-blue/30 border-t-cyan"
      />
      <span>{label}</span>
    </div>
  );
}
