// トースト通知（軽量）。useToast() で成功/エラーを表示。
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

interface ToastItem { id: number; message: string; kind: "info" | "error"; }
interface ToastCtx { notify: (message: string, kind?: "info" | "error") => void; }

const Ctx = createContext<ToastCtx | null>(null);
let seq = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const notify = useCallback((message: string, kind: "info" | "error" = "info") => {
    const id = ++seq;
    setItems((s) => [...s, { id, message, kind }]);
    window.setTimeout(() => setItems((s) => s.filter((t) => t.id !== id)), 3200);
  }, []);
  const value = useMemo(() => ({ notify }), [notify]);
  return (
    <Ctx.Provider value={value}>
      {children}
      <div className="toast-wrap" aria-live="polite">
        {items.map((t) => (
          <div key={t.id} className={`toast ${t.kind === "error" ? "error" : ""}`}>{t.message}</div>
        ))}
      </div>
    </Ctx.Provider>
  );
}

export function useToast(): ToastCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useToast must be used within <ToastProvider>");
  return ctx;
}
