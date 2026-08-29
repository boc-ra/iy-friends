// U3 公開API クライアント。VITE_API_BASE_URL 未設定時はダミーデータで動作（Q-P4=A）。
import { dummyEvents, dummyNotices, dummyPosts } from "./dummy";
import type {
  ContactInput,
  EventDetail,
  EventSummary,
  ListResult,
  Notice,
  NoticeSummary,
  Post,
  PostSummary,
} from "./types";

const BASE = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "";
export const USING_DUMMY = BASE === "";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { headers: { Accept: "application/json" } });
  if (!res.ok) {
    throw new ApiError(res.status, `リクエストに失敗しました (${res.status})`);
  }
  return (await res.json()) as T;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// ---- Posts ----
export async function listPosts(cursor?: string): Promise<ListResult<PostSummary>> {
  if (USING_DUMMY) {
    return { items: dummyPosts.map(toPostSummary), next_cursor: null };
  }
  const q = cursor ? `?cursor=${encodeURIComponent(cursor)}` : "";
  return getJson(`/posts${q}`);
}

export async function getPost(id: string): Promise<Post> {
  if (USING_DUMMY) {
    const found = dummyPosts.find((p) => p.post_id === id);
    if (!found) throw new ApiError(404, "記事が見つかりません");
    return found;
  }
  return getJson(`/posts/${encodeURIComponent(id)}`);
}

// ---- Notices ----
export async function listNotices(cursor?: string): Promise<ListResult<NoticeSummary>> {
  if (USING_DUMMY) {
    return { items: dummyNotices.map(toNoticeSummary), next_cursor: null };
  }
  const q = cursor ? `?cursor=${encodeURIComponent(cursor)}` : "";
  return getJson(`/notices${q}`);
}

export async function getNotice(id: string): Promise<Notice> {
  if (USING_DUMMY) {
    const found = dummyNotices.find((n) => n.notice_id === id);
    if (!found) throw new ApiError(404, "お知らせが見つかりません");
    return found;
  }
  return getJson(`/notices/${encodeURIComponent(id)}`);
}

// ---- Events ----
export async function listEvents(cursor?: string): Promise<ListResult<EventSummary>> {
  if (USING_DUMMY) {
    return { items: dummyEvents.map(toEventSummary), next_cursor: null };
  }
  const q = cursor ? `?cursor=${encodeURIComponent(cursor)}` : "";
  return getJson(`/events${q}`);
}

// カレンダーは月内の全予定を表示するため、全ページを取得する（上限12ページ=安全弁）。
export async function listAllEvents(): Promise<EventSummary[]> {
  const all: EventSummary[] = [];
  let cursor: string | undefined;
  for (let i = 0; i < 12; i++) {
    const res = await listEvents(cursor);
    all.push(...res.items);
    if (!res.next_cursor) break;
    cursor = res.next_cursor;
  }
  return all;
}

// ---- Contact ----
export async function submitContact(input: ContactInput): Promise<{ status: string }> {
  if (USING_DUMMY) {
    await new Promise((r) => setTimeout(r, 400));
    return { status: "accepted" };
  }
  const res = await fetch(`${BASE}/contact`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    throw new ApiError(res.status, res.status === 400 ? "入力内容をご確認ください" : "送信に失敗しました");
  }
  return (await res.json()) as { status: string };
}

// ---- helpers ----
function toPostSummary(p: Post): PostSummary {
  const { post_id, title, author_display_name, category, published_at } = p;
  return { post_id, title, author_display_name, category, published_at };
}
function toNoticeSummary(n: Notice): NoticeSummary {
  return { notice_id: n.notice_id, title: n.title, published_at: n.published_at };
}
function toEventSummary(e: EventDetail): EventSummary {
  return { event_id: e.event_id, title: e.title, description: e.description, location: e.location, event_date: e.event_date };
}
