import type { Attempt } from "../types";

export function ErrorModal({
  attempt,
  onClose,
}: {
  attempt: Attempt | null;
  onClose: () => void;
}) {
  if (!attempt) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Scrape Attempt Details</h3>
          <button className="btn-icon" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <p><strong>Attempt Number:</strong> #{attempt.attempt_number}</p>
          <p><strong>Status:</strong> <span className="text-danger">{attempt.status}</span></p>
          <p><strong>Timestamp:</strong> {attempt.attempted_at ? new Date(attempt.attempted_at).toLocaleString() : "-"}</p>
          {attempt.error_code && <p><strong>Error Code:</strong> <code>{attempt.error_code}</code></p>}
          <div className="error-detail-block">
            <strong>Error Message:</strong>
            <pre>{attempt.error_message || "No error details provided."}</pre>
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}
