import { Link } from "react-router-dom";
import { listNotices, listPosts } from "../api/client";
import { ErrorState, Loading } from "../components/States";
import { useAsync } from "../hooks/useAsync";
import { formatDate } from "../lib/format";

export function Home() {
  const posts = useAsync(() => listPosts(), []);
  const notices = useAsync(() => listNotices(), []);

  return (
    <>
      <section className="hero">
        <div className="container fade-in">
          <h1 className="display">楽しく、一生懸命に！！</h1>
          <p className="lead" style={{ marginTop: "var(--sp-4)" }}>
            IYフレンズは横浜市栄区で活動するミニバスケットボールチームです。
            上郷小学校の体育館を中心に、1年生〜6年生の男女がのびのび練習しています。
            初めてのお子さまも大歓迎。見学・体験はいつでもどうぞ。
          </p>
          <div style={{ display: "flex", gap: "var(--sp-3)", marginTop: "var(--sp-8)", flexWrap: "wrap" }}>
            <Link to="/join" className="btn" data-testid="home-cta-join">入会・体験のご案内</Link>
            <Link to="/contact" className="btn secondary" data-testid="home-cta-contact">お問い合わせ</Link>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
            <h2>スタッフの声</h2>
            <Link to="/blog" className="muted">すべて見る →</Link>
          </div>
          {posts.loading && <Loading />}
          {posts.error && <ErrorState message={posts.error} />}
          {posts.data && (
            <div className="grid" style={{ marginTop: "var(--sp-6)" }}>
              {posts.data.items.slice(0, 3).map((p) => (
                <Link key={p.post_id} to={`/blog/${p.post_id}`} className="card entry-card" data-testid="home-post">
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

      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container">
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
            <h2>お知らせ</h2>
            <Link to="/notices" className="muted">すべて見る →</Link>
          </div>
          {notices.loading && <Loading />}
          {notices.error && <ErrorState message={notices.error} />}
          {notices.data && (
            <ul className="stack" style={{ marginTop: "var(--sp-6)" }}>
              {notices.data.items.slice(0, 4).map((n) => (
                <li key={n.notice_id} className="card entry-card">
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
