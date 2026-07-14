/**
 * Date formatting utilities.
 * Pure functions — no React dependency.
 */

const dateTimeFormatter = new Intl.DateTimeFormat('en-GB', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
});

function parseDate(iso: string | null | undefined): Date | null {
  if (!iso) return null;
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? null : date;
}

/**
 * Format an ISO date string as "YYYY/MM/DD HH:MM".
 * Returns fallback for null/undefined/invalid input.
 */
export function formatDateTime(
  iso: string | null | undefined,
  fallback = '—',
): string {
  const date = parseDate(iso);
  if (!date) return fallback;

  const parts = dateTimeFormatter.formatToParts(date);
  const get = (type: Intl.DateTimeFormatPartTypes): string =>
    parts.find((p) => p.type === type)?.value ?? '';

  return `${get('year')}/${get('month')}/${get('day')} ${get('hour')}:${get('minute')}`;
}

/**
 * Format an ISO date string as a relative time: "just now", "2m ago", "3h ago", "1d ago".
 * Falls back to formatDateTime for dates older than 30 days.
 */
export function formatRelativeTime(iso: string | null | undefined): string {
  const date = parseDate(iso);
  if (!date) return '—';

  const diffMs = Date.now() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);

  if (diffSec < 60) return 'just now';

  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;

  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;

  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 30) return `${diffDay}d ago`;

  return formatDateTime(iso);
}

/**
 * Format the duration between two ISO date strings.
 * If end is omitted, uses current time.
 * Returns "Xh Ym", "Ym Zs", or "Zs" depending on magnitude.
 */
export function formatDuration(
  start: string | null | undefined,
  end?: string | null | undefined,
): string {
  const startDate = parseDate(start);
  if (!startDate) return '—';

  const endDate = end ? parseDate(end) : new Date();
  if (!endDate) return '—';

  const diffMs = endDate.getTime() - startDate.getTime();
  if (diffMs < 0) return '—';

  const totalSec = Math.floor(diffMs / 1000);
  const hours = Math.floor(totalSec / 3600);
  const minutes = Math.floor((totalSec % 3600) / 60);
  const seconds = totalSec % 60;

  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m ${seconds}s`;
  return `${seconds}s`;
}
