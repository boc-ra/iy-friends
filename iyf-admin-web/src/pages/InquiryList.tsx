// 問い合わせ一覧（Admin）。対応状況で絞り込み。
import { useState } from "react";
import { Link } from "react-router-dom";
import { listInquiries } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { formatDateTime } from "../lib/format";
import { EmptyState, ErrorState, Loading, Select, StatusBadge } from "../components/ui";

export function InquiryList() {
  const [status, setStatus] = useState<string>("");
  const { data, loading, error, reload } = useAsync(() => listInquiries(status ? { status } : {}), [status]);

  return (
    <>
      <div className="page-header"><h1>問い合わせ</h1></div>

      <div className="field" style={{ maxWidth: "12rem", marginBottom: "var(--sp-4)" }}>
        <Select value={status} onChange={(e) => setStatus(e.target.value)} data-testid="inquiry-filter">
          <option value="">すべて</option>
          <option value="未対応">未対応</option>
          <option value="対応中">対応中</option>
          <option value="対応済">対応済</option>
        </Select>
      </div>

      {loading && <Loading />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && data.items.length === 0 && <EmptyState message="問い合わせはありません。" />}
      {data && (
        <div className="list">
          {data.items.map((i) => (
            <Link key={i.inquiry_id} to={`/inquiries/${i.inquiry_id}`} className="row-card" data-testid="inquiry-row">
              <span className="grow">
                <span className="title">{i.name}</span>
                <span className="sub">{i.email}・{formatDateTime(i.created_at)}</span>
              </span>
              <StatusBadge status={i.status} />
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
