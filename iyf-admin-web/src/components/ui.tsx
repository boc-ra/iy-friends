// 小さなUIプリミティブ（apple-design・スマホ最適化）。
import type { ReactNode, InputHTMLAttributes, TextareaHTMLAttributes, SelectHTMLAttributes, ButtonHTMLAttributes } from "react";
import type { PublishStatus, InquiryStatus } from "../api/types";

export function Button({ variant = "primary", small, children, ...rest }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "danger"; small?: boolean }) {
  const cls = ["btn", variant === "secondary" ? "secondary" : "", variant === "danger" ? "danger-btn" : "", small ? "small" : ""].filter(Boolean).join(" ");
  return <button className={cls} {...rest}>{children}</button>;
}

export function Field({ label, htmlFor, hint, error, children }: { label: string; htmlFor?: string; hint?: string; error?: string; children: ReactNode }) {
  return (
    <div className="field">
      <label htmlFor={htmlFor}>{label}</label>
      {children}
      {hint && !error && <span className="hint">{hint}</span>}
      {error && <span className="err">{error}</span>}
    </div>
  );
}

export function TextField(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input className="input" {...props} />;
}
export function TextArea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className="textarea" {...props} />;
}
export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className="select" {...props} />;
}

const STATUS_LABEL: Record<string, string> = {
  draft: "下書き", published: "公開中",
  未対応: "未対応", 対応中: "対応中", 対応済: "対応済",
};
export function StatusBadge({ status }: { status: PublishStatus | InquiryStatus }) {
  const key = String(status);
  return <span className={`badge ${key}`}>{STATUS_LABEL[key] ?? key}</span>;
}

export function Loading({ label = "読み込み中…" }: { label?: string }) {
  return <p className="muted" role="status">{label}</p>;
}
export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="card" style={{ padding: "var(--sp-6)" }}>
      <p className="danger">{message}</p>
      {onRetry && <Button variant="secondary" small onClick={onRetry}>再試行</Button>}
    </div>
  );
}
export function EmptyState({ message }: { message: string }) {
  return <p className="muted" style={{ padding: "var(--sp-6) 0" }}>{message}</p>;
}
