// ユーザー管理（Admin）: 一覧・編集者招待・有効/無効。
import { useState } from "react";
import { inviteEditor, listUsers, setUserStatus } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { useToast } from "../components/Toast";
import { Button, EmptyState, ErrorState, Field, Loading, TextField } from "../components/ui";
import { ConfirmDialog } from "../components/ConfirmDialog";
import type { UserSummary } from "../api/types";

export function UserList() {
  const { notify } = useToast();
  const { data, loading, error, reload } = useAsync(() => listUsers(), []);
  const [email, setEmail] = useState("");
  const [inviting, setInviting] = useState(false);
  const [inviteErr, setInviteErr] = useState<string | null>(null);
  const [toDisable, setToDisable] = useState<UserSummary | null>(null);

  const invite = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviteErr(null);
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { setInviteErr("メールアドレスの形式が正しくありません。"); return; }
    setInviting(true);
    try { await inviteEditor(email.trim()); notify("招待メールを送信しました。"); setEmail(""); reload(); }
    catch (err) { const m = err instanceof Error ? err.message : "招待に失敗しました。"; setInviteErr(m); notify(m, "error"); }
    finally { setInviting(false); }
  };

  const toggle = async (u: UserSummary) => {
    if (u.status === "active") { setToDisable(u); return; }
    try { await setUserStatus(u.user_id, "active"); notify("有効にしました。"); reload(); }
    catch (err) { notify(err instanceof Error ? err.message : "更新に失敗しました。", "error"); }
  };

  const confirmDisable = async () => {
    if (!toDisable) return;
    const u = toDisable; setToDisable(null);
    try { await setUserStatus(u.user_id, "disabled"); notify("無効にしました。"); reload(); }
    catch (err) { notify(err instanceof Error ? err.message : "更新に失敗しました。", "error"); }
  };

  return (
    <>
      <div className="page-header"><h1>ユーザー</h1></div>

      <form className="card stack" style={{ padding: "var(--sp-6)", maxWidth: "32rem", marginBottom: "var(--sp-8)" }} onSubmit={invite}>
        <h2 style={{ fontSize: "1.1rem" }}>編集者を招待</h2>
        <Field label="メールアドレス" htmlFor="invite" error={inviteErr ?? undefined}>
          <TextField id="invite" type="email" value={email} onChange={(e) => setEmail(e.target.value)} data-testid="invite-email" />
        </Field>
        <Button type="submit" disabled={inviting} data-testid="invite-submit">{inviting ? "送信中…" : "招待メールを送る"}</Button>
      </form>

      {loading && <Loading />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && data.items.length === 0 && <EmptyState message="ユーザーがいません。" />}
      {data && (
        <div className="list">
          {data.items.map((u) => (
            <div key={u.user_id} className="row-card" data-testid="user-row">
              <span className="grow">
                <span className="title">{u.display_name ?? "（表示名未設定）"}</span>
                <span className="sub">{u.email}・{u.role === "admin" ? "管理者" : "編集者"}{u.profile_state === "pending" ? "・招待中" : ""}</span>
              </span>
              <span className={`badge ${u.status === "active" ? "published" : "done"}`}>{u.status === "active" ? "有効" : "無効"}</span>
              {u.role !== "admin" && (
                <Button variant="secondary" small onClick={() => toggle(u)} data-testid="user-toggle">
                  {u.status === "active" ? "無効化" : "有効化"}
                </Button>
              )}
            </div>
          ))}
        </div>
      )}

      <ConfirmDialog open={!!toDisable} title="このユーザーを無効化しますか？" message="無効化するとログインできなくなります（既存の記事は残ります）。" confirmLabel="無効化する" onConfirm={confirmDisable} onCancel={() => setToDisable(null)} />
    </>
  );
}
