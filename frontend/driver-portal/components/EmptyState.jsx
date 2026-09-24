import "./EmptyState.css";

export default function EmptyState({
  title = "Nothing here yet",
  message,
  actionLabel,
  onAction,
}) {
  return (
    <div className="empty-state surface">
      <div className="empty-state-mark" aria-hidden="true">
        <svg viewBox="0 0 32 32" width="26" height="26">
          <circle cx="16" cy="16" r="12" fill="none" stroke="currentColor" strokeWidth="2" />
          <path d="M16 10v7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          <circle cx="16" cy="21.5" r="1.4" fill="currentColor" />
        </svg>
      </div>
      <h3>{title}</h3>
      {message && <p>{message}</p>}
      {actionLabel && onAction && (
        <button type="button" className="btn btn-primary" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </div>
  );
}
