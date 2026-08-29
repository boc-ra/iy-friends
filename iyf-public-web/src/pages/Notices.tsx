import { listNotices } from "../api/client";
import { EmptyState, ErrorState, Loading } from "../components/States";
import { useAsync } from "../hooks/useAsync";
import { formatDate } from "../lib/format";

export function Notices() {
  const { loading, data, error } = useAsync(() => listNotices(), []);

  return (
    <>
      <div className="page-head">
        <div className="container">
          <h1>お知らせ</h1>
          <p className="lead">練習・会費・行事などの大切なご連絡です。</p>
        </div>
      </div>
      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container narrow">
          {loading && <Loading />}
          {error && <ErrorState message={error} />}
          {data && data.items.length === 0 && <EmptyState message="お知らせはありません。" />}
          {data && data.items.length > 0 && (
            <ul className="stack">
              {data.items.map((n) => (
                <li key={n.notice_id} className="card entry-card" data-testid="notice-item">
                  <div className="meta"><span>{formatDate(n.published_at)}</span></div>
                  <h3>{n.title}</h3>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </>
  );
}
