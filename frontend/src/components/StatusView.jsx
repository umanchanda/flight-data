export function LoadingState({ message = 'Loading…' }) {
  return <div className="status-card">{message}</div>
}

export function ErrorState({ message }) {
  return <div className="status-card status-card-error">{message}</div>
}
