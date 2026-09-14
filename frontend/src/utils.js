export function formatDate(value) {
  if (!value) return '—'
  return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function formatTime(value) {
  if (!value) return '—'
  return value.slice(0, 5)
}

export function formatHours(value) {
  if (value == null || Number.isNaN(value)) return '—'
  return `${Number(value).toFixed(1)} h`
}

export function formatDurationMinutes(value) {
  if (value == null) return '—'
  return (value / 60).toFixed(1)
}
