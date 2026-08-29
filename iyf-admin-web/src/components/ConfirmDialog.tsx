// 削除など破壊的操作の確認ダイアログ（アラート/confirm は使わない）。
import { Button } from "./ui";

export function ConfirmDialog({ open, title, message, confirmLabel = "削除する", onConfirm, onCancel }: {
  open: boolean; title: string; message?: string; confirmLabel?: string;
  onConfirm: () => void; onCancel: () => void;
}) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3 style={{ marginBottom: "var(--sp-3)" }}>{title}</h3>
        {message && <p className="muted" style={{ marginBottom: "var(--sp-6)" }}>{message}</p>}
        <div className="inline" style={{ justifyContent: "flex-end", gap: "var(--sp-3)" }}>
          <Button variant="secondary" onClick={onCancel} data-testid="confirm-cancel">キャンセル</Button>
          <Button variant="danger" onClick={onConfirm} data-testid="confirm-ok">{confirmLabel}</Button>
        </div>
      </div>
    </div>
  );
}
