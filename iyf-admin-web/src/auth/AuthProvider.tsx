// 認証コンテキスト（Amplify v6 + ダミー）。
// フロー: signedOut → [newPassword] → [mfa | mfaSetup] → signedIn。
// admin は MFA 未登録なら mfaSetup を強制（U5 infra §3, MfaConfiguration=OPTIONAL の補完）。
import {
  confirmSignIn,
  fetchAuthSession,
  fetchMFAPreference,
  getCurrentUser,
  setUpTOTP,
  signIn as amplifySignIn,
  signOut as amplifySignOut,
  updateMFAPreference,
  verifyTOTPSetup,
} from "aws-amplify/auth";
import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { DUMMY_AUTH, setDummyToken } from "./amplifyConfig";

export type Role = "admin" | "editor";
export type AuthStatus = "loading" | "signedOut" | "newPassword" | "mfa" | "mfaSetup" | "signedIn";

export interface AuthUser {
  sub: string;
  email: string;
  role: Role;
}

export interface AuthContextValue {
  status: AuthStatus;
  user: AuthUser | null;
  error: string | null;
  mfaSetupUri: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  submitNewPassword: (password: string) => Promise<void>;
  submitMfaCode: (code: string) => Promise<void>;
  verifyMfaSetup: (code: string) => Promise<void>;
  signOut: () => Promise<void>;
  clearError: () => void;
  // ダミーモードのロール切替（画面確認用）。
  dummyRole: Role;
  setDummyRole: (r: Role) => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

function roleFromGroups(groups: unknown): Role {
  const arr = Array.isArray(groups) ? groups.map(String) : typeof groups === "string" ? [groups] : [];
  if (arr.includes("admin")) return "admin";
  return "editor";
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<AuthUser | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mfaSetupUri, setMfaSetupUri] = useState<string | null>(null);
  const [enforcedSetup, setEnforcedSetup] = useState(false);
  const [dummyRole, setDummyRoleState] = useState<Role>("admin");

  const clearError = useCallback(() => setError(null), []);

  // ---- 認証済みユーザーを確定して signedIn にする（MFA 判定はしない） ----
  const resolveUser = useCallback(async () => {
    const session = await fetchAuthSession();
    const payload = session.tokens?.accessToken?.payload ?? {};
    const role = roleFromGroups((payload as Record<string, unknown>)["cognito:groups"]);
    const current = await getCurrentUser();
    setUser({ sub: current.userId, email: current.signInDetails?.loginId ?? "", role });
    setStatus("signedIn");
  }, []);

  // ---- セッション確定（DONE 後）: admin×MFA未登録なら強制登録へ ----
  const finalize = useCallback(async () => {
    const session = await fetchAuthSession();
    const payload = session.tokens?.accessToken?.payload ?? {};
    const role = roleFromGroups((payload as Record<string, unknown>)["cognito:groups"]);
    const current = await getCurrentUser();
    if (role === "admin") {
      const pref = await fetchMFAPreference();
      const hasTotp = pref.enabled?.includes("TOTP");
      if (!hasTotp) {
        const totp = await setUpTOTP();
        setMfaSetupUri(totp.getSetupUri("IYフレンズ管理", current.signInDetails?.loginId).toString());
        setEnforcedSetup(true);
        setUser({ sub: current.userId, email: current.signInDetails?.loginId ?? "", role });
        setStatus("mfaSetup");
        return;
      }
    }
    setUser({ sub: current.userId, email: current.signInDetails?.loginId ?? "", role });
    setStatus("signedIn");
  }, []);

  // ---- 初期化：既存セッションの復元 ----
  useEffect(() => {
    let active = true;
    (async () => {
      if (DUMMY_AUTH) {
        setStatus("signedOut");
        return;
      }
      try {
        await getCurrentUser();
        if (active) await finalize();
      } catch {
        if (active) setStatus("signedOut");
      }
    })();
    return () => {
      active = false;
    };
  }, [finalize]);

  // ---- サインイン ----
  const signIn = useCallback(async (email: string, password: string) => {
    setError(null);
    if (DUMMY_AUTH) {
      setDummyToken(`dummy-${dummyRole}-token`);
      setUser({ sub: `dummy-${dummyRole}`, email, role: dummyRole });
      setStatus("signedIn");
      return;
    }
    try {
      const { nextStep } = await amplifySignIn({ username: email, password });
      await routeNextStep(nextStep);
    } catch (e) {
      setError(errMsg(e, "ログインに失敗しました。メールアドレスとパスワードをご確認ください。"));
    }
  }, [dummyRole]);

  const routeNextStep = useCallback(async (nextStep: { signInStep: string; totpSetupDetails?: { getSetupUri: (app: string) => URL } }) => {
    switch (nextStep.signInStep) {
      case "CONFIRM_SIGN_IN_WITH_NEW_PASSWORD_REQUIRED":
        setStatus("newPassword");
        break;
      case "CONFIRM_SIGN_IN_WITH_TOTP_CODE":
        setStatus("mfa");
        break;
      case "CONTINUE_SIGN_IN_WITH_TOTP_SETUP":
        setMfaSetupUri(nextStep.totpSetupDetails?.getSetupUri("IYフレンズ管理").toString() ?? null);
        setEnforcedSetup(false);
        setStatus("mfaSetup");
        break;
      case "DONE":
        await finalize();
        break;
      default:
        setError("追加の認証手順に対応していません。");
    }
  }, [finalize]);

  const submitNewPassword = useCallback(async (password: string) => {
    setError(null);
    try {
      const { nextStep } = await confirmSignIn({ challengeResponse: password });
      await routeNextStep(nextStep);
    } catch (e) {
      setError(errMsg(e, "新しいパスワードを設定できませんでした。"));
    }
  }, [routeNextStep]);

  const submitMfaCode = useCallback(async (code: string) => {
    setError(null);
    try {
      const { nextStep } = await confirmSignIn({ challengeResponse: code });
      await routeNextStep(nextStep);
    } catch (e) {
      setError(errMsg(e, "認証コードが正しくありません。"));
    }
  }, [routeNextStep]);

  const verifyMfaSetup = useCallback(async (code: string) => {
    setError(null);
    try {
      if (enforcedSetup) {
        await verifyTOTPSetup({ code });
        await updateMFAPreference({ totp: "PREFERRED" });
        setMfaSetupUri(null);
        setEnforcedSetup(false);
        // 登録済みなので MFA 再判定はせず直接 signedIn へ（再ループ防止）。
        await resolveUser();
      } else {
        const { nextStep } = await confirmSignIn({ challengeResponse: code });
        await routeNextStep(nextStep);
      }
    } catch (e) {
      setError(errMsg(e, "認証アプリのコードを確認できませんでした。"));
    }
  }, [enforcedSetup, resolveUser, routeNextStep]);

  const signOut = useCallback(async () => {
    if (DUMMY_AUTH) {
      setDummyToken(null);
      setUser(null);
      setStatus("signedOut");
      return;
    }
    await amplifySignOut();
    setUser(null);
    setStatus("signedOut");
  }, []);

  const setDummyRole = useCallback((r: Role) => setDummyRoleState(r), []);

  const value = useMemo<AuthContextValue>(() => ({
    status, user, error, mfaSetupUri,
    signIn, submitNewPassword, submitMfaCode, verifyMfaSetup, signOut, clearError,
    dummyRole, setDummyRole,
  }), [status, user, error, mfaSetupUri, signIn, submitNewPassword, submitMfaCode, verifyMfaSetup, signOut, clearError, dummyRole, setDummyRole]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

function errMsg(e: unknown, fallback: string): string {
  if (e && typeof e === "object" && "message" in e && typeof (e as { message: unknown }).message === "string") {
    return (e as { message: string }).message || fallback;
  }
  return fallback;
}
