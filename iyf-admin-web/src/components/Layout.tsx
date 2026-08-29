// 認証済みの枠（TopBar + ロール別 NavDrawer + Outlet）。スマホはドロワー開閉。
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import { Button } from "./ui";

interface NavItem { to: string; label: string; adminOnly?: boolean; }
const NAV: NavItem[] = [
  { to: "/", label: "ダッシュボード" },
  { to: "/posts", label: "ブログ" },
  { to: "/notices", label: "お知らせ" },
  { to: "/calendar", label: "カレンダー" },
  { to: "/inquiries", label: "問い合わせ", adminOnly: true },
  { to: "/users", label: "ユーザー", adminOnly: true },
  { to: "/profile", label: "プロフィール" },
];

export function Layout() {
  const { user, signOut } = useAuth();
  const [open, setOpen] = useState(false);
  const isAdmin = user?.role === "admin";
  const items = NAV.filter((n) => !n.adminOnly || isAdmin);

  const nav = (onClick?: () => void) => (
    <nav>
      {items.map((n) => (
        <NavLink key={n.to} to={n.to} end={n.to === "/"} onClick={onClick}
          className={({ isActive }) => (isActive ? "active" : "")} data-testid={`nav-${n.to.replace(/\//g, "") || "home"}`}>
          {n.label}
        </NavLink>
      ))}
    </nav>
  );

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="icon-btn menu" aria-label="メニュー" onClick={() => setOpen(true)} data-testid="menu-open">☰</button>
        <span className="brand">IYフレンズ 管理</span>
        <span className="spacer" />
        <span className="user">{user?.email} {isAdmin ? "（管理者）" : "（編集者）"}</span>
        <Button variant="secondary" small onClick={signOut} data-testid="signout">ログアウト</Button>
      </header>

      <div className="layout">
        <aside className="drawer static">{nav()}</aside>
        {open && (
          <>
            <div className="drawer-backdrop" onClick={() => setOpen(false)} />
            <aside className="drawer mobile">{nav(() => setOpen(false))}</aside>
          </>
        )}
        <main className="main">
          <div className="container">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
