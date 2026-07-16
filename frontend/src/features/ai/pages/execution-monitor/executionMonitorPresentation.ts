const STATUS_CLASS: Record<string, string> = {
  RUNNING: 'running',
  WAITING: 'waiting',
  SUCCEEDED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'ended',
  BLOCKED: 'waiting',
}

export function statusClass(status: string): string {
  return STATUS_CLASS[status] || 'pending'
}

export function formatTime(value?: string | null): string {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

export function formatDuration(start?: string | null, end?: string | null): string {
  if (!start) return '-'
  const endDate = end ? new Date(end) : new Date()
  const milliseconds = Math.max(0, endDate.getTime() - new Date(start).getTime())
  const seconds = Math.round(milliseconds / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${minutes}m`
  return `${Math.round(minutes / 60)}h`
}
