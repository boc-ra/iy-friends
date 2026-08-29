// 自分の表示名（displayName）設定。初回ログイン後に必須（未設定だと投稿系が 409）。
import { useState } from "react";
import { completeProfile } from "../api/client";
import { useToast } from "../components/Toast";
import { Button, Field, TextField } from "../components/ui";

export function Profile() {
  const { notify } = useToast();
  const [displayName, setDisplayName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (displayName.trim().length < 1 || displayName.length > 40) {
      setError("表示名は1〜40文字で入力してください。");
      return;
    }
    setSaving(true);
    try {
      await completeProfile(displayName.trim());
      notify("表示名を保存しました。投稿できるようになりました。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存に失敗しました。");
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <div className="page-header"><h1>プロフィール</h1></div>
      <p className="muted" style={{ marginBottom: "var(--sp-4)" }}>
        記事の著者として表示される名前です。初回は必ず設定してください（未設定だと記事の作成・公開ができません）。
      </p>
      <form className="stack card" style={{ padding: "var(--sp-6)", maxWidth: "28rem" }} onSubmit={submit}>
        <Field label="表示名" htmlFor="dn" hint="例: コーチ山田" error={error ?? undefined}>
          <TextField id="dn" required maxLength={40} value={displayName} onChange={(e) => setDisplayName(e.target.value)} data-testid="profile-displayname" />
        </Field>
        <Button type="submit" disabled={saving} data-testid="profile-save">{saving ? "保存中…" : "保存する"}</Button>
      </form>
    </>
  );
}
