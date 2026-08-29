import { useMemo, useState } from "react";
import { listAllEvents } from "../api/client";
import { EmptyState, ErrorState, Loading } from "../components/States";
import { useAsync } from "../hooks/useAsync";
import { formatDateTime } from "../lib/format";
import type { EventSummary } from "../api/types";

const DOW = ["日", "月", "火", "水", "木", "金", "土"];
const JST = "Asia/Tokyo";

// ISO日時 → JSTの "YYYY-MM-DD" キー
function jstKey(iso: string): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: JST, year: "numeric", month: "2-digit", day: "2-digit",
  }).format(new Date(iso));
}
const pad = (n: number) => String(n).padStart(2, "0");
const keyOf = (y: number, m: number, d: number) => `${y}-${pad(m)}-${pad(d)}`;

// タイトルから色分け用の種別を推定
function kind(title: string): "rest" | "meeting" | "practice" {
  if (title.includes("休み")) return "rest";
  if (title.includes("保護者会")) return "meeting";
  return "practice";
}

// 説明の先頭にある時間帯（例 "18:45〜21:00"）を取り出す
function timeOf(desc?: string): string {
  const m = (desc ?? "").match(/^\s*(\d{1,2}:\d{2}\s*[〜~-]\s*\d{1,2}:\d{2})/);
  return m ? m[1].replace(/\s/g, "") : "";
}

export function Calendar() {
  const { loading, data, error } = useAsync(() => listAllEvents(), []);

  // 日付キー → その日のイベント
  const byDay = useMemo(() => {
    const map = new Map<string, EventSummary[]>();
    for (const e of data ?? []) {
      const k = jstKey(e.event_date);
      (map.get(k) ?? map.set(k, []).get(k)!).push(e);
    }
    return map;
  }, [data]);

  // 表示する年月（既定：最初の予定の月、なければ今日）
  const initial = useMemo(() => {
    const src = data && data.length > 0 ? jstKey(data[0].event_date) : jstKey(new Date().toISOString());
    const [y, m] = src.split("-").map(Number);
    return { y, m };
  }, [data]);
  const [ym, setYm] = useState<{ y: number; m: number } | null>(null);
  const cur = ym ?? initial;

  const move = (delta: number) => {
    const d = new Date(Date.UTC(cur.y, cur.m - 1 + delta, 1));
    setYm({ y: d.getUTCFullYear(), m: d.getUTCMonth() + 1 });
  };

  // グリッド構築（TZ非依存でUTC基準に日付を計算）
  const firstDow = new Date(Date.UTC(cur.y, cur.m - 1, 1)).getUTCDay();
  const daysInMonth = new Date(Date.UTC(cur.y, cur.m, 0)).getUTCDate();
  const cells: (number | null)[] = [
    ...Array(firstDow).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];
  while (cells.length % 7 !== 0) cells.push(null);
  const todayKey = jstKey(new Date().toISOString());

  // その月の予定（下部リスト用）
  const monthEvents = (data ?? [])
    .filter((e) => jstKey(e.event_date).startsWith(`${cur.y}-${pad(cur.m)}`))
    .sort((a, b) => a.event_date.localeCompare(b.event_date));

  return (
    <>
      <div className="page-head">
        <div className="container">
          <h1>活動予定</h1>
          <p className="lead">練習や試合など、活動の予定です。</p>
        </div>
      </div>
      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container narrow">
          {loading && <Loading />}
          {error && <ErrorState message={error} />}
          {data && (
            <>
              <div className="cal-head">
                <button className="cal-nav" onClick={() => move(-1)} aria-label="前の月" data-testid="cal-prev">‹</button>
                <strong>{cur.y}年{cur.m}月</strong>
                <button className="cal-nav" onClick={() => move(1)} aria-label="次の月" data-testid="cal-next">›</button>
              </div>

              <div className="cal-grid" role="grid">
                {DOW.map((d, i) => (
                  <div key={d} className={`cal-dow ${i === 0 ? "sun" : ""} ${i === 6 ? "sat" : ""}`}>{d}</div>
                ))}
                {cells.map((d, idx) => {
                  if (d === null) return <div key={`e${idx}`} className="cal-cell empty" />;
                  const k = keyOf(cur.y, cur.m, d);
                  const evs = byDay.get(k) ?? [];
                  const dow = idx % 7;
                  return (
                    <div key={k} className={`cal-cell ${k === todayKey ? "today" : ""}`}>
                      <span className={`cal-day ${dow === 0 ? "sun" : ""} ${dow === 6 ? "sat" : ""}`}>{d}</span>
                      {evs.map((e) => {
                        const t = timeOf(e.description);
                        return (
                          <div key={e.event_id} className={`cal-ev ${kind(e.title)}`} title={e.title}>
                            <span className="cal-ev-title">{e.title}</span>
                            {t && <span className="cal-ev-sub">{t}</span>}
                            {e.location && <span className="cal-ev-sub loc">{e.location}</span>}
                          </div>
                        );
                      })}
                    </div>
                  );
                })}
              </div>

              <h2 style={{ margin: "var(--sp-8) 0 var(--sp-4)" }}>{cur.m}月の予定</h2>
              {monthEvents.length === 0 && <EmptyState message="この月の予定はありません。" />}
              {monthEvents.length > 0 && (
                <ul className="stack">
                  {monthEvents.map((e) => (
                    <li key={e.event_id} className="card entry-card" data-testid="event-item">
                      <div className="meta">
                        <span>{formatDateTime(e.event_date)}</span>
                        {e.location && <span>· {e.location}</span>}
                      </div>
                      <h3>{e.title}</h3>
                      {e.description && <p className="muted" style={{ margin: 0 }}>{e.description}</p>}
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </div>
      </section>
    </>
  );
}
