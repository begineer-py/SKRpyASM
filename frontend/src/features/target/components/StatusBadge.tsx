interface StatusBadgeProps {
  status: string;
}

const STATUS_COLORS: Record<string, string> = {
  PLANNING: "cyan", EXECUTING: "green", STALLED: "amber",
  COMPLETED: "green", PENDING: "muted", RUNNING: "cyan",
  FAILED: "red", OPEN: "green", CLOSED: "muted", FILTERED: "amber",
};

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const c = STATUS_COLORS[status?.toUpperCase()] ?? "muted";
  return <span className={`c2-badge c2-badge--${c}`}>{status}</span>;
};

export default StatusBadge;
