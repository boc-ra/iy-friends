import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer className="site-footer">
      <div className="container cols">
        <div className="stack">
          <strong style={{ color: "var(--c-text)" }}>IYフレンズ</strong>
          <p className="muted">横浜市栄区のミニバスケットボールチーム。<br />楽しく、一生懸命に！！</p>
        </div>
        <nav className="stack" aria-label="フッターナビゲーション">
          <Link to="/about">クラブ紹介</Link>
          <Link to="/join">メンバー募集</Link>
          <Link to="/terms">部費・規約</Link>
          <Link to="/contact">お問い合わせ</Link>
        </nav>
      </div>
      <div className="container" style={{ marginTop: "var(--sp-8)" }}>
        <small className="muted">© {new Date().getFullYear()} IYフレンズ</small>
      </div>
    </footer>
  );
}
