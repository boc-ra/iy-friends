// U3 AdminApi クライアント。access token を Authorization に付与。
// VITE_API_BASE_URL 未設定時はダミーモード（バックエンド/Cognito 無しで動作）。
import { getAccessToken } from "../auth/session";
import * as dummy from "./dummy";
import type {
  EventInput,
  EventItem,
  Inquiry,
  InquiryStatus,
  InquirySummary,
  ListResult,
  Notice,
  NoticeInput,
  NoticeSummary,
  Post,
  PostInput,
  PostSummary,
  PublishStatus,
  UserSummary,
} from "./types";

const BASE = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "";
export const USING_DUMMY = BASE === "";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function messageFor(status: number): string {
  switch (status) {
    case 401: return "セッションが切れました。再度ログインしてください。";
    case 403: return "この操作を行う権限がありません。";
    case 404: return "対象が見つかりません。";
    case 409: return "現在の状態では実行できません（プロフィール未完了など）。";
    case 422: return "入力内容をご確認ください。";
    case 429: return "リクエストが多すぎます。しばらくお待ちください。";
    default: return `リクエストに失敗しました (${status})`;
  }
}

async function authFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getAccessToken();
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(init.body ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(init.headers as Record<string, string> | undefined),
  };
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!res.ok) throw new ApiError(res.status, messageFor(res.status));
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

const qs = (params: Record<string, string | undefined>) => {
  const p = Object.entries(params).filter(([, v]) => v != null && v !== "");
  return p.length ? `?${p.map(([k, v]) => `${k}=${encodeURIComponent(v as string)}`).join("&")}` : "";
};

// ================= Posts =================
export const listPostsAdmin = (o: { status?: string; cursor?: string } = {}): Promise<ListResult<PostSummary>> =>
  USING_DUMMY ? dummy.listPosts(o.status) : authFetch(`/admin/posts${qs(o)}`);
export const getPostAdmin = (id: string): Promise<Post> =>
  USING_DUMMY ? dummy.getPost(id) : authFetch(`/admin/posts/${encodeURIComponent(id)}`);
export const createPost = (input: PostInput): Promise<Post> =>
  USING_DUMMY ? dummy.createPost(input) : authFetch(`/admin/posts`, { method: "POST", body: JSON.stringify(input) });
export const updatePost = (id: string, input: PostInput): Promise<Post> =>
  USING_DUMMY ? dummy.updatePost(id, input) : authFetch(`/admin/posts/${encodeURIComponent(id)}`, { method: "PUT", body: JSON.stringify(input) });
export const deletePost = (id: string): Promise<void> =>
  USING_DUMMY ? dummy.remove("post", id) : authFetch(`/admin/posts/${encodeURIComponent(id)}`, { method: "DELETE" });
export const setPostStatus = (id: string, status: PublishStatus): Promise<Post> =>
  USING_DUMMY ? dummy.setPostStatus(id, status) : authFetch(`/admin/posts/${encodeURIComponent(id)}/status`, { method: "PUT", body: JSON.stringify({ status }) });

// ================= Notices =================
export const listNoticesAdmin = (o: { status?: string; cursor?: string } = {}): Promise<ListResult<NoticeSummary>> =>
  USING_DUMMY ? dummy.listNotices(o.status) : authFetch(`/admin/notices${qs(o)}`);
export const getNoticeAdmin = (id: string): Promise<Notice> =>
  USING_DUMMY ? dummy.getNotice(id) : authFetch(`/admin/notices/${encodeURIComponent(id)}`);
export const createNotice = (input: NoticeInput): Promise<Notice> =>
  USING_DUMMY ? dummy.createNotice(input) : authFetch(`/admin/notices`, { method: "POST", body: JSON.stringify(input) });
export const updateNotice = (id: string, input: NoticeInput): Promise<Notice> =>
  USING_DUMMY ? dummy.updateNotice(id, input) : authFetch(`/admin/notices/${encodeURIComponent(id)}`, { method: "PUT", body: JSON.stringify(input) });
export const deleteNotice = (id: string): Promise<void> =>
  USING_DUMMY ? dummy.remove("notice", id) : authFetch(`/admin/notices/${encodeURIComponent(id)}`, { method: "DELETE" });
export const setNoticeStatus = (id: string, status: PublishStatus): Promise<Notice> =>
  USING_DUMMY ? dummy.setNoticeStatus(id, status) : authFetch(`/admin/notices/${encodeURIComponent(id)}/status`, { method: "PUT", body: JSON.stringify({ status }) });

// ================= Events =================
export const listEventsAdmin = (o: { status?: string; cursor?: string } = {}): Promise<ListResult<EventItem>> =>
  USING_DUMMY ? dummy.listEvents(o.status) : authFetch(`/admin/events${qs(o)}`);
export const createEvent = (input: EventInput): Promise<EventItem> =>
  USING_DUMMY ? dummy.createEvent(input) : authFetch(`/admin/events`, { method: "POST", body: JSON.stringify(input) });
export const updateEvent = (id: string, input: EventInput): Promise<EventItem> =>
  USING_DUMMY ? dummy.updateEvent(id, input) : authFetch(`/admin/events/${encodeURIComponent(id)}`, { method: "PUT", body: JSON.stringify(input) });
export const deleteEvent = (id: string): Promise<void> =>
  USING_DUMMY ? dummy.remove("event", id) : authFetch(`/admin/events/${encodeURIComponent(id)}`, { method: "DELETE" });

// ================= Inquiries (admin) =================
export const listInquiries = (o: { status?: string } = {}): Promise<ListResult<InquirySummary>> =>
  USING_DUMMY ? dummy.listInquiries(o.status) : authFetch(`/admin/inquiries${qs(o)}`);
export const getInquiry = (id: string): Promise<Inquiry> =>
  USING_DUMMY ? dummy.getInquiry(id) : authFetch(`/admin/inquiries/${encodeURIComponent(id)}`);
export const setInquiryStatus = (id: string, status: InquiryStatus): Promise<Inquiry> =>
  USING_DUMMY ? dummy.setInquiryStatus(id, status) : authFetch(`/admin/inquiries/${encodeURIComponent(id)}/status`, { method: "PUT", body: JSON.stringify({ status }) });

// ================= Users (admin) =================
export const listUsers = (): Promise<{ items: UserSummary[] }> =>
  USING_DUMMY ? dummy.listUsers() : authFetch(`/admin/users`);
export const inviteEditor = (email: string): Promise<UserSummary> =>
  USING_DUMMY ? dummy.inviteEditor(email) : authFetch(`/admin/users/invite`, { method: "POST", body: JSON.stringify({ email }) });
export const setUserStatus = (id: string, status: "active" | "disabled"): Promise<UserSummary> =>
  USING_DUMMY ? dummy.setUserStatus(id, status) : authFetch(`/admin/users/${encodeURIComponent(id)}/status`, { method: "PUT", body: JSON.stringify({ status }) });

// ================= Profile =================
export const completeProfile = (display_name: string): Promise<UserSummary> =>
  USING_DUMMY ? dummy.completeProfile(display_name) : authFetch(`/admin/me/profile`, { method: "PUT", body: JSON.stringify({ display_name }) });
