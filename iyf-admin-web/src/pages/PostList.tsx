// ブログ一覧（draft含む・状態バッジ）。
import { useState } from "react";
import { Link } from "react-router-dom";
import { listPostsAdmin } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { formatDate } from "../lib/format";
import { EmptyState, ErrorState, Loading, Select, StatusBadge } from "../components/ui";

export function PostList() {
  const [status, setStatus] = useState<string>("");
  const { data, loading, error, reload } = useAsync(() => listPostsAdmin(status ? { status } : {}), [status]);

  return (
    <>
      <div className="page-header">
        <h1>ブログ</h1>
        <span className="spacer" />
        <Link className="btn" to="/posts/new" data-testid="new-post">新規作成</Link>
      </div>

      <div className="field" style={{ maxWidth: "12rem", marginBottom: "var(--sp-4)" }}>
        <Select value={status} onChange={(e) => setStatus(e.target.value)} data-testid="post-filter">
          <option value="">すべて</option>
          <option value="draft">下書き</option>
          <option value="published">公開中</option>
        </Select>
      </div>

      {loading && <Loading />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && data.items.length === 0 && <EmptyState message="記事がありません。" />}
      {data && (
        <div className="list">
          {data.items.map((p) => (
            <Link key={p.post_id} to={`/posts/${p.post_id}`} className="row-card" data-testid="post-row">
              <span className="grow">
                <span className="title">{p.title}</span>
                <span className="sub">{formatDate(p.published_at ?? p.updated_at)}</span>
              </span>
              <StatusBadge status={p.status} />
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
