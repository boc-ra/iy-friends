// ログイン（SRP→新パスワード→MFA入力→MFA登録）。ダミーモードは擬似ログイン。
import { useState } from "react";
import { Navigate } from "react-router-dom";
import { DUMMY_AUTH } from "../auth/amplifyConfig";
import { useAuth } from "../auth/useAuth";
import { Button, Field, Select, TextField } from "../components/ui";

export function Login() {
  const auth = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [newPw, setNewPw] = useState("");
  const [code, setCode] = useState("");

  if (auth.status === "signedIn") return <Navigate to="/" replace />;

  return (
    <div className="auth-wrap">
      <div className="auth-card stack">
        <h1 style={{ fontSize: "1.6rem" }}>IYフレンズ 管理画面</h1>

        {auth.error && <p className="err" role="alert">{auth.error}</p>}

        {auth.status === "signedOut" || auth.status === "loading" ? (
          <form className="stack" onSubmit={(e) => { e.preventDefault(); auth.signIn(email, password); }}>
            {DUMMY_AUTH && (
              <Field label="ロール（ダミー確認用）">
                <Select value={auth.dummyRole} onChange={(e) => auth.setDummyRole(e.target.value as "admin" | "editor")} data-testid="dummy-role">
                  <option value="admin">admin（管理者）</option>
                  <option value="editor">editor（編集者）</option>
                </Select>
              </Field>
            )}
            <Field label="メールアドレス" htmlFor="email">
              <TextField id="email" type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} data-testid="login-email" />
            </Field>
            <Field label="パスワード" htmlFor="pw">
              <TextField id="pw" type="password" autoComplete="current-password" required={!DUMMY_AUTH} value={password} onChange={(e) => setPassword(e.target.value)} data-testid="login-password" />
            </Field>
            <Button type="submit" data-testid="login-submit">ログイン</Button>
          </form>
        ) : null}

        {auth.status === "newPassword" && (
          <form className="stack" onSubmit={(e) => { e.preventDefault(); auth.submitNewPassword(newPw); }}>
            <p className="muted">初回ログインです。新しいパスワードを設定してください。</p>
            <Field label="新しいパスワード" htmlFor="npw">
              <TextField id="npw" type="password" autoComplete="new-password" required value={newPw} onChange={(e) => setNewPw(e.target.value)} data-testid="new-password" />
            </Field>
            <Button type="submit" data-testid="new-password-submit">設定して続ける</Button>
          </form>
        )}

        {auth.status === "mfa" && (
          <form className="stack" onSubmit={(e) => { e.preventDefault(); auth.submitMfaCode(code); }}>
            <p className="muted">認証アプリの6桁コードを入力してください。</p>
            <Field label="認証コード" htmlFor="mfa">
              <TextField id="mfa" inputMode="numeric" autoComplete="one-time-code" required value={code} onChange={(e) => setCode(e.target.value)} data-testid="mfa-code" />
            </Field>
            <Button type="submit" data-testid="mfa-submit">確認</Button>
          </form>
        )}

        {auth.status === "mfaSetup" && (
          <form className="stack" onSubmit={(e) => { e.preventDefault(); auth.verifyMfaSetup(code); }}>
            <p className="muted">管理者は多要素認証（MFA）の登録が必要です。スマホの認証アプリ（Google Authenticator 等）で、下の<strong>セットアップキー</strong>を「手動で入力／セットアップキーを入力」から登録してください。</p>
            {auth.mfaSetupUri && (
              <div className="field">
                <label>セットアップキー（認証アプリに手入力）</label>
                <code style={{ display: "block", padding: "var(--sp-3)", background: "var(--c-surface)", borderRadius: "10px", wordBreak: "break-all", letterSpacing: "0.05em" }} data-testid="mfa-secret">
                  {secretFromUri(auth.mfaSetupUri)}
                </code>
                <span className="hint">
                  アカウント種別は「時間ベース(TOTP)」。うまくいかない場合は
                  <a href={auth.mfaSetupUri} style={{ textDecoration: "underline" }}> このリンク</a>
                  をスマホで開くと自動登録できます。
                </span>
              </div>
            )}
            <Field label="認証アプリに表示された6桁コード" htmlFor="setup">
              <TextField id="setup" inputMode="numeric" autoComplete="one-time-code" required value={code} onChange={(e) => setCode(e.target.value)} data-testid="mfa-setup-code" />
            </Field>
            <Button type="submit" data-testid="mfa-setup-submit">登録して続ける</Button>
          </form>
        )}
      </div>
    </div>
  );
}

// otpauth://totp/LABEL?secret=BASE32&issuer=... から手入力用の secret を取り出す。
function secretFromUri(uri: string): string {
  try {
    const q = uri.split("?")[1] ?? "";
    const params = new URLSearchParams(q);
    return params.get("secret") ?? uri;
  } catch {
    return uri;
  }
}
