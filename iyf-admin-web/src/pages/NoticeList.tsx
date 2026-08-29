// お知らせ一覧（draft含む）。
import { useState } from "react";
import { Link } from "react-router-dom";
import { listNoticesAdmin } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { formatDate } from "../lib/format";
import { EmptyState, ErrorState, Loading, Select, StatusBadge } from "../components/ui";

export function NoticeList() {
  const [status, setStatus] = useState<string>("");
  const { data, loading, error, reload } = useAsync(() => listNoticesAdmin(status ? { status } : {}), [status]);

  return (
    <>
      <div className="page-header">
        <h1>お知らせ</h1>
        <span className="spacer" />
        <Link className="btn" to="/notices/new" data-testid="new-notice">新規作成</Link>
      </div>

      <div className="field" style={{ maxWidth: "12rem", marginBottom: "var(--sp-4)" }}>
        <Select value={status} onChange={(e) => setStatus(e.target.value)} data-testid="notice-filter">
          <option value="">すべて</option>
          <option value="draft">下書き</option>
          <option value="published">公開中</option>
        </Select>
      </div>

      {loading && <Loading />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && data.items.length === 0 && <EmptyState message="お知らせがありません。" />}
      {data && (
        <div className="list">
          {data.items.map((n) => (
            <Link key={n.notice_id} to={`/notices/${n.notice_id}`} className="row-card" data-testid="notice-row">
              <span className="grow">
                <span className="title">{n.title}</span>
                <span className="sub">{formatDate(n.published_at ?? n.updated_at)}</span>
              </span>
              <StatusBadge status={n.status} />
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
