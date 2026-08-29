// アクセストークン取得（api/client が利用）。
import { fetchAuthSession } from "aws-amplify/auth";
import { DUMMY_AUTH, getDummyToken } from "./amplifyConfig";

export async function getAccessToken(): Promise<string | null> {
  if (DUMMY_AUTH) return getDummyToken();
  try {
    const session = await fetchAuthSession();
    return session.tokens?.accessToken?.toString() ?? null;
  } catch {
    return null;
  }
}
