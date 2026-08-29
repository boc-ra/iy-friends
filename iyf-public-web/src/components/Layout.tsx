import { useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { USING_DUMMY } from "../api/client";
import { Footer } from "./Footer";
import { Header } from "./Header";

export function Layout() {
  const { pathname } = useLocation();

  // ページ遷移時に先頭へ（フォーカス管理・ワイヤーfinding）。
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "auto" });
  }, [pathname]);

  return (
    <>
      {USING_DUMMY && (
        <div className="demo-banner" role="status">
          デモ表示中（サンプルデータ）。実データは API 接続後に表示されます。
        </div>
      )}
      <Header />
      <main id="main">
        <Outlet />
      </main>
      <Footer />
    </>
  );
}
