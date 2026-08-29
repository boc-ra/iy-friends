// Amplify（Cognito）設定。env 未設定時はダミー認証モード。
import { Amplify } from "aws-amplify";

export const USER_POOL_ID = import.meta.env.VITE_USER_POOL_ID ?? "";
export const USER_POOL_CLIENT_ID = import.meta.env.VITE_USER_POOL_CLIENT_ID ?? "";

// UserPool 未設定 → ダミー認証（バックエンド/Cognito 無しで画面確認）。
export const DUMMY_AUTH = USER_POOL_ID === "" || USER_POOL_CLIENT_ID === "";

export function configureAmplify(): void {
  if (DUMMY_AUTH) return;
  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId: USER_POOL_ID,
        userPoolClientId: USER_POOL_CLIENT_ID,
      },
    },
  });
}

// ダミーモードのアクセストークン保持（api/client が Authorization に使う）。
let _dummyToken: string | null = null;
export const setDummyToken = (t: string | null): void => {
  _dummyToken = t;
};
export const getDummyToken = (): string | null => _dummyToken;
