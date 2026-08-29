// ダッシュボード: 主要導線＋自分の下書き。
import { Link } from "react-router-dom";
import { listPostsAdmin } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { EmptyState, ErrorState, Loading, StatusBadge } from "../components/ui";

export function Dashboard() {
  const { data, loading, error, reload } = useAsync(() => listPostsAdmin({ status: "draft" }), []);

  return (
    <>
      <div className="page-header"><h1>ダッシュボード</h1></div>

      <div className="grid-cards" style={{ marginBottom: "var(--sp-8)" }}>
        <Link className="card" style={{ padding: "var(--sp-6)" }} to="/posts/new" data-testid="quick-new-post"><strong>ブログを書く</strong><p className="muted">新しい記事を作成</p></Link>
        <Link className="card" style={{ padding: "var(--sp-6)" }} to="/notices/new"><strong>お知らせを書く</strong><p className="muted">連絡事項を掲載</p></Link>
        <Link className="card" style={{ padding: "var(--sp-6)" }} to="/calendar/new"><strong>予定を追加</strong><p className="muted">練習・試合など</p></Link>
      </div>

      <h2 style={{ marginBottom: "var(--sp-4)" }}>下書き</h2>
      {loading && <Loading />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && data.items.length === 0 && <EmptyState message="下書きはありません。" />}
      {data && data.items.length > 0 && (
        <div className="list">
          {data.items.map((p) => (
            <Link key={p.post_id} to={`/posts/${p.post_id}`} className="row-card">
              <span className="grow"><span className="title">{p.title}</span></span>
              <StatusBadge status={p.status} />
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
