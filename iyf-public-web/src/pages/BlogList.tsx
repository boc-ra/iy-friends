import { Link } from "react-router-dom";
import { listPosts } from "../api/client";
import { EmptyState, ErrorState, Loading } from "../components/States";
import { useAsync } from "../hooks/useAsync";
import { formatDate } from "../lib/format";

export function BlogList() {
  const { loading, data, error } = useAsync(() => listPosts(), []);

  return (
    <>
      <div className="page-head">
        <div className="container">
          <h1>スタッフの声</h1>
          <p className="lead">監督・コーチ・スタッフから、日々の活動の様子をお届けします。</p>
        </div>
      </div>
      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container">
          {loading && <Loading />}
          {error && <ErrorState message={error} />}
          {data && data.items.length === 0 && <EmptyState message="まだ記事がありません。" />}
          {data && data.items.length > 0 && (
            <div className="grid">
              {data.items.map((p) => (
                <Link key={p.post_id} to={`/blog/${p.post_id}`} className="card entry-card" data-testid="blog-item">
                  <div className="meta">
                    {p.category && <span className="tag">{p.category}</span>}
                    <span>{formatDate(p.published_at)}</span>
                  </div>
                  <h3>{p.title}</h3>
                  <span className="muted">{p.author_display_name}</span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>
    </>
  );
}
