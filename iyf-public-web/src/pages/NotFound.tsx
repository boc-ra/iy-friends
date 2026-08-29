import { Link } from "react-router-dom";

export function NotFound() {
  return (
    <section className="section">
      <div className="container narrow state">
        <h1>ページが見つかりません</h1>
        <p className="muted">お探しのページは移動または削除された可能性があります。</p>
        <div style={{ marginTop: "var(--sp-6)" }}>
          <Link to="/" className="btn" data-testid="notfound-home">ホームへ戻る</Link>
        </div>
      </div>
    </section>
  );
}
