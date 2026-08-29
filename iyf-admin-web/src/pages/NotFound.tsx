import { Link } from "react-router-dom";

export function NotFound() {
  return (
    <div className="stack" style={{ padding: "var(--sp-12) 0" }}>
      <h1>ページが見つかりません</h1>
      <p className="muted">お探しのページは存在しないか、移動しました。</p>
      <Link className="btn" to="/">ダッシュボードへ</Link>
    </div>
  );
}
