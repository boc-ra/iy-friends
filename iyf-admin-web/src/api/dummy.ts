// ダミーデータ＋擬似操作（バックエンド/Cognito 無しで画面確認）。
// 実運用では VITE_API_BASE_URL を設定し client.ts の authFetch 経路が使われる。
import type {
  EventInput, EventItem, Inquiry, InquiryStatus, InquirySummary, ListResult,
  Notice, NoticeInput, NoticeSummary, Post, PostInput, PostSummary,
  PublishStatus, UserSummary,
} from "./types";

const now = () => new Date().toISOString();
const id = () => (globalThis.crypto?.randomUUID?.() ?? `id-${Date.now()}-${Math.floor(Math.random() * 1e6)}`);

let posts: Post[] = [
  { post_id: "p1", title: "夏の合同練習を実施しました", body: "<p>市民体育館で合同練習を行いました。ドリブルとシュートの基礎を中心に…</p>", author_display_name: "コーチ山田", author_id: "u-editor", status: "published", published_at: now(), updated_at: now() },
  { post_id: "p2", title: "（下書き）交流大会のふりかえり", body: "<p>さくらミニバスとの交流大会について…</p>", author_display_name: "コーチ山田", author_id: "u-editor", status: "draft", updated_at: now() },
];
let notices: Notice[] = [
  { notice_id: "n1", title: "9月の練習日程について", body: "<p>9月の練習は毎週土曜9時からです。</p>", status: "published", published_at: now(), updated_at: now(), author_id: "u-admin" },
];
let events: EventItem[] = [
  { event_id: "e1", title: "練習（基礎）", description: "ドリブル・シュート", location: "市民体育館", event_date: new Date(Date.now() + 86400000 * 7).toISOString(), status: "published" },
];
let inquiries: Inquiry[] = [
  { inquiry_id: "i1", name: "保護者A", email: "parent-a@example.com", message: "体験入部について知りたいです。", status: "未対応", created_at: now() },
];
let users: UserSummary[] = [
  { user_id: "u-admin", email: "admin@example.com", display_name: "管理者", role: "admin", status: "active", profile_state: "complete", created_at: now() },
  { user_id: "u-editor", email: "coach@example.com", display_name: "コーチ山田", role: "editor", status: "active", profile_state: "complete", created_at: now() },
];

const wrap = <T>(items: T[]): ListResult<T> => ({ items, next_cursor: null });
const byStatus = <T extends { status: string }>(arr: T[], status?: string) => (status ? arr.filter((x) => x.status === status) : arr);

// ---- Posts ----
export const listPosts = async (status?: string): Promise<ListResult<PostSummary>> =>
  wrap(byStatus(posts, status).map((p) => ({ post_id: p.post_id, title: p.title, status: p.status, updated_at: p.updated_at, author_id: p.author_id, published_at: p.published_at })));
export const getPost = async (pid: string): Promise<Post> => {
  const p = posts.find((x) => x.post_id === pid);
  if (!p) throw new Error("not found");
  return p;
};
export const createPost = async (input: PostInput): Promise<Post> => {
  const p: Post = { post_id: id(), author_display_name: "自分", author_id: "u-editor", updated_at: now(), published_at: input.status === "published" ? now() : null, ...input };
  posts = [p, ...posts];
  return p;
};
export const updatePost = async (pid: string, input: PostInput): Promise<Post> => {
  posts = posts.map((p) => (p.post_id === pid ? { ...p, ...input, updated_at: now(), published_at: input.status === "published" ? p.published_at ?? now() : p.published_at } : p));
  return getPost(pid);
};
export const setPostStatus = async (pid: string, status: PublishStatus): Promise<Post> => {
  posts = posts.map((p) => (p.post_id === pid ? { ...p, status, updated_at: now(), published_at: status === "published" ? p.published_at ?? now() : p.published_at } : p));
  return getPost(pid);
};

// ---- Notices ----
export const listNotices = async (status?: string): Promise<ListResult<NoticeSummary>> =>
  wrap(byStatus(notices, status).map((n) => ({ notice_id: n.notice_id, title: n.title, status: n.status, updated_at: n.updated_at, author_id: n.author_id, published_at: n.published_at })));
export const getNotice = async (nid: string): Promise<Notice> => {
  const n = notices.find((x) => x.notice_id === nid);
  if (!n) throw new Error("not found");
  return n;
};
export const createNotice = async (input: NoticeInput): Promise<Notice> => {
  const n: Notice = { notice_id: id(), author_id: "u-admin", updated_at: now(), published_at: input.status === "published" ? now() : null, ...input };
  notices = [n, ...notices];
  return n;
};
export const updateNotice = async (nid: string, input: NoticeInput): Promise<Notice> => {
  notices = notices.map((n) => (n.notice_id === nid ? { ...n, ...input, updated_at: now() } : n));
  return getNotice(nid);
};
export const setNoticeStatus = async (nid: string, status: PublishStatus): Promise<Notice> => {
  notices = notices.map((n) => (n.notice_id === nid ? { ...n, status, updated_at: now(), published_at: status === "published" ? n.published_at ?? now() : n.published_at } : n));
  return getNotice(nid);
};

// ---- Events ----
export const listEvents = async (status?: string): Promise<ListResult<EventItem>> => wrap(byStatus(events, status));
export const createEvent = async (input: EventInput): Promise<EventItem> => {
  const e: EventItem = { event_id: id(), ...input };
  events = [...events, e];
  return e;
};
export const updateEvent = async (eid: string, input: EventInput): Promise<EventItem> => {
  events = events.map((e) => (e.event_id === eid ? { ...e, ...input } : e));
  const e = events.find((x) => x.event_id === eid);
  if (!e) throw new Error("not found");
  return e;
};

// ---- Inquiries ----
export const listInquiries = async (status?: string): Promise<ListResult<InquirySummary>> =>
  wrap(byStatus(inquiries, status).map((i) => ({ inquiry_id: i.inquiry_id, name: i.name, email: i.email, status: i.status, created_at: i.created_at, updated_at: i.updated_at })));
export const getInquiry = async (iid: string): Promise<Inquiry> => {
  const i = inquiries.find((x) => x.inquiry_id === iid);
  if (!i) throw new Error("not found");
  return i;
};
export const setInquiryStatus = async (iid: string, status: InquiryStatus): Promise<Inquiry> => {
  inquiries = inquiries.map((i) => (i.inquiry_id === iid ? { ...i, status, updated_at: now() } : i));
  return getInquiry(iid);
};

// ---- Users ----
export const listUsers = async (): Promise<{ items: UserSummary[] }> => ({ items: users });
export const inviteEditor = async (email: string): Promise<UserSummary> => {
  const u: UserSummary = { user_id: id(), email: email.toLowerCase(), display_name: null, role: "editor", status: "active", profile_state: "pending", created_at: now() };
  users = [...users, u];
  return u;
};
export const setUserStatus = async (uid: string, status: "active" | "disabled"): Promise<UserSummary> => {
  users = users.map((u) => (u.user_id === uid ? { ...u, status } : u));
  const u = users.find((x) => x.user_id === uid);
  if (!u) throw new Error("not found");
  return u;
};
export const completeProfile = async (display_name: string): Promise<UserSummary> => ({
  user_id: "u-self", email: "self@example.com", display_name, role: "editor", status: "active", profile_state: "complete", created_at: now(),
});

// ---- 汎用削除 ----
export const remove = async (kind: "post" | "notice" | "event", rid: string): Promise<void> => {
  if (kind === "post") posts = posts.filter((p) => p.post_id !== rid);
  if (kind === "notice") notices = notices.filter((n) => n.notice_id !== rid);
  if (kind === "event") events = events.filter((e) => e.event_id !== rid);
};
