// U3 公開API の型（api-documentation.md に対応）

export interface PostSummary {
  post_id: string;
  title: string;
  author_display_name: string;
  category: string | null;
  published_at: string | null;
}

export interface Post extends PostSummary {
  body: string;
  source?: string;
  source_url?: string | null;
}

export interface NoticeSummary {
  notice_id: string;
  title: string;
  published_at: string | null;
}

export interface Notice extends NoticeSummary {
  body: string;
}

export interface EventSummary {
  event_id: string;
  title: string;
  description?: string;
  location: string | null;
  event_date: string;
}

export interface EventDetail extends EventSummary {
  description: string;
}

export interface ListResult<T> {
  items: T[];
  next_cursor: string | null;
}

export interface ContactInput {
  name: string;
  email: string;
  message: string;
}
