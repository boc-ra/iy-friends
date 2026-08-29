// カレンダー管理（共有編集: 誰でも任意の予定を編集/削除可）。
import { Link } from "react-router-dom";
import { listEventsAdmin } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { formatDateTime } from "../lib/format";
import { EmptyState, ErrorState, Loading, StatusBadge } from "../components/ui";

export function CalendarAdmin() {
  const { data, loading, error, reload } = useAsync(() => listEventsAdmin(), []);

  return (
    <>
      <div className="page-header">
        <h1>カレンダー</h1>
        <span className="spacer" />
        <Link className="btn" to="/calendar/new" data-testid="new-event">予定を追加</Link>
      </div>

      {loading && <Loading />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && data.items.length === 0 && <EmptyState message="予定がありません。" />}
      {data && (
        <div className="list">
          {data.items.map((e) => (
            <Link key={e.event_id} to={`/calendar/${e.event_id}`} className="row-card" data-testid="event-row">
              <span className="grow">
                <span className="title">{e.title}</span>
                <span className="sub">{formatDateTime(e.event_date)}{e.location ? `・${e.location}` : ""}</span>
              </span>
              <StatusBadge status={e.status} />
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
