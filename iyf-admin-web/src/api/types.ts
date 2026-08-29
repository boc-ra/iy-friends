// U3 AdminApi のデータ型。

export type PublishStatus = "draft" | "published";
export type InquiryStatus = "未対応" | "対応中" | "対応済";
export type Role = "admin" | "editor";
export type UserStatus = "active" | "disabled";

export interface ListResult<T> {
  items: T[];
  next_cursor: string | null;
}

// ---- Post / Notice ----
export interface Post {
  post_id: string;
  title: string;
  body: string;
  author_display_name: string;
  author_id?: string | null;
  category?: string | null;
  status: PublishStatus;
  published_at?: string | null;
  updated_at?: string | null;
}
export interface PostSummary {
  post_id: string;
  title: string;
  status: PublishStatus;
  updated_at?: string | null;
  author_id?: string | null;
  published_at?: string | null;
}
export interface PostInput {
  title: string;
  body: string;
  category?: string | null;
  status: PublishStatus;
}

export interface Notice {
  notice_id: string;
  title: string;
  body: string;
  status: PublishStatus;
  published_at?: string | null;
  updated_at?: string | null;
  author_id?: string | null;
}
export interface NoticeSummary {
  notice_id: string;
  title: string;
  status: PublishStatus;
  updated_at?: string | null;
  author_id?: string | null;
  published_at?: string | null;
}
export interface NoticeInput {
  title: string;
  body: string;
  status: PublishStatus;
}

// ---- Event ----
export interface EventItem {
  event_id: string;
  title: string;
  description?: string;
  location?: string | null;
  event_date: string;
  status: PublishStatus;
}
export interface EventInput {
  title: string;
  description?: string;
  location?: string | null;
  event_date: string;
  status: PublishStatus;
}

// ---- Inquiry ----
export interface Inquiry {
  inquiry_id: string;
  name: string;
  email: string;
  message: string;
  status: InquiryStatus;
  created_at: string;
  updated_at?: string | null;
  updated_by?: string | null;
}
export interface InquirySummary {
  inquiry_id: string;
  name: string;
  email: string;
  status: InquiryStatus;
  created_at: string;
  updated_at?: string | null;
}

// ---- User ----
export interface UserSummary {
  user_id: string;
  email: string;
  display_name: string | null;
  role: Role;
  status: UserStatus;
  profile_state: "pending" | "complete";
  created_at?: string | null;
}
