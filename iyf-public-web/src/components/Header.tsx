import { useState } from "react";
import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "ホーム", end: true },
  { to: "/blog", label: "スタッフの声" },
  { to: "/notices", label: "お知らせ" },
  { to: "/calendar", label: "活動予定" },
  { to: "/about", label: "紹介" },
  { to: "/join", label: "メンバー募集" },
  { to: "/terms", label: "部費・規約" },
  { to: "/contact", label: "お問い合わせ" },
];

export function Header() {
  const [open, setOpen] = useState(false);

  return (
    <header className="site-header">
      <div className="container bar">
        <NavLink to="/" className="brand" data-testid="header-brand" onClick={() => setOpen(false)}>
          <span className="dot" aria-hidden="true" />
          <strong>IYフレンズ</strong>
        </NavLink>

        <button
          className="nav-toggle"
          aria-label="メニューを開閉"
          aria-expanded={open}
          data-testid="header-nav-toggle"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? "✕" : "☰"}
        </button>

        <nav className={`nav ${open ? "open" : ""}`} aria-label="メインナビゲーション">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              data-testid={`nav-${l.to === "/" ? "home" : l.to.slice(1)}`}
              className={({ isActive }) => (isActive ? "active" : "")}
              onClick={() => setOpen(false)}
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
