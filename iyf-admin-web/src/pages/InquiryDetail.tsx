// 問い合わせ詳細・対応状況の更新（Admin）。
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getInquiry, setInquiryStatus } from "../api/client";
import { useToast } from "../components/Toast";
import { Button, Field, Loading, Select } from "../components/ui";
import { formatDateTime } from "../lib/format";
import type { Inquiry, InquiryStatus } from "../api/types";

const STATUSES: InquiryStatus[] = ["未対応", "対応中", "対応済"];

export function InquiryDetail() {
  const { id } = useParams();
  const { notify } = useToast();
  const [inq, setInq] = useState<Inquiry | null>(null);
  const [status, setStatus] = useState<InquiryStatus>("未対応");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getInquiry(id!)
      .then((i) => { setInq(i); setStatus(i.status); })
      .catch((e) => setError(e instanceof Error ? e.message : "読み込みに失敗しました。"))
      .finally(() => setLoading(false));
  }, [id]);

  const save = async () => {
    setSaving(true);
    try { const updated = await setInquiryStatus(id!, status); setInq(updated); notify("対応状況を更新しました。"); }
    catch (e) { notify(e instanceof Error ? e.message : "更新に失敗しました。", "error"); }
    finally { setSaving(false); }
  };

  if (loading) return <Loading />;
  if (error) return <p className="err">{error}</p>;
  if (!inq) return null;

  return (
    <>
      <div className="page-header"><h1>問い合わせ詳細</h1></div>
      <div className="card stack" style={{ padding: "var(--sp-6)", maxWidth: "40rem" }}>
        <div><span className="muted">お名前</span><p className="title">{inq.name}</p></div>
        <div><span className="muted">メール</span><p><a href={`mailto:${inq.email}`}>{inq.email}</a></p></div>
        <div><span className="muted">受信日時</span><p>{formatDateTime(inq.created_at)}</p></div>
        <div><span className="muted">本文</span><p style={{ whiteSpace: "pre-wrap" }}>{inq.message}</p></div>
        <Field label="対応状況" htmlFor="st">
          <Select id="st" value={status} onChange={(e) => setStatus(e.target.value as InquiryStatus)} data-testid="inquiry-status-select">
            {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </Select>
        </Field>
        <Button onClick={save} disabled={saving} data-testid="inquiry-status-save">更新する</Button>
      </div>
    </>
  );
}
