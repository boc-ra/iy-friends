// 読み込み・エラー・空表示の共通コンポーネント。

export function Loading({ label = "読み込み中…" }: { label?: string }) {
  return (
    <div className="state" role="status" aria-live="polite" data-testid="loading">
      <div className="spinner" aria-hidden="true" />
      {label}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="state" role="alert" data-testid="error">
      <p>{message}</p>
      <p className="muted">時間をおいて再度お試しください。</p>
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="state" data-testid="empty">
      <p>{message}</p>
    </div>
  );
}
