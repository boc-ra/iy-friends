import { Link, useParams } from "react-router-dom";
import { getPost } from "../api/client";
import { ErrorState, Loading } from "../components/States";
import { useAsync } from "../hooks/useAsync";
import { formatDate } from "../lib/format";

export function BlogDetail() {
  const { id = "" } = useParams();
  const { loading, data, error } = useAsync(() => getPost(id), [id]);

  return (
    <article className="section">
      <div className="container narrow">
        <Link to="/blog" className="muted" data-testid="blog-back">← ブログ一覧へ</Link>
        {loading && <Loading />}
        {error && <ErrorState message={error} />}
        {data && (
          <div className="prose fade-in" style={{ marginTop: "var(--sp-6)" }}>
            <div className="meta" style={{ display: "flex", gap: "var(--sp-2)", color: "var(--c-text-muted)" }}>
              {data.category && <span className="tag">{data.category}</span>}
              <span>{formatDate(data.published_at)}</span>
            </div>
            <h1 style={{ marginTop: "var(--sp-3)" }}>{data.title}</h1>
            <p className="muted">{data.author_display_name}</p>
            <p>{data.body}</p>
          </div>
        )}
      </div>
    </article>
  );
}
