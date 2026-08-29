// 予定の作成/編集（共有編集）。日時は datetime-local（JST 前提）で入力し ISO(+09:00) で送信。
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { createEvent, deleteEvent, listEventsAdmin, updateEvent } from "../api/client";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { useToast } from "../components/Toast";
import { Button, Field, Loading, Select, TextArea, TextField } from "../components/ui";
import type { EventInput } from "../api/types";

// ISO(+09:00) ⇄ datetime-local("YYYY-MM-DDThh:mm")
const toLocal = (iso: string): string => (iso ? iso.slice(0, 16) : "");
const toIso = (local: string): string => (local ? `${local}:00+09:00` : "");

export function EventEdit() {
  const { id } = useParams();
  const isNew = !id;
  const nav = useNavigate();
  const { notify } = useToast();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [dateLocal, setDateLocal] = useState("");
  const [status, setStatus] = useState<"draft" | "published">("published");
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [confirmDel, setConfirmDel] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isNew) return;
    // 一覧から該当予定を取得（イベント個別GETは未提供のため一覧から特定）。
    listEventsAdmin()
      .then((r) => {
        const e = r.items.find((x) => x.event_id === id);
        if (!e) throw new Error("予定が見つかりません。");
        setTitle(e.title); setDescription(e.description ?? ""); setLocation(e.location ?? "");
        setDateLocal(toLocal(e.event_date)); setStatus(e.status);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "読み込みに失敗しました。"))
      .finally(() => setLoading(false));
  }, [id, isNew]);

  const input = (): EventInput => ({ title: title.trim(), description: description.trim(), location: location.trim() || null, event_date: toIso(dateLocal), status });

  const handleError = (e: unknown) => {
    const msg = e instanceof Error ? e.message : "保存に失敗しました。";
    setError(msg); notify(msg, "error");
  };

  const save = async () => {
    setError(null);
    if (title.trim().length < 1) { setError("タイトルを入力してください。"); return; }
    if (!dateLocal) { setError("日時を入力してください。"); return; }
    setSaving(true);
    try {
      if (isNew) { await createEvent(input()); notify("予定を追加しました。"); }
      else { await updateEvent(id!, input()); notify("保存しました。"); }
      nav("/calendar");
    } catch (e) { handleError(e); } finally { setSaving(false); }
  };

  const doDelete = async () => {
    setConfirmDel(false);
    try { await deleteEvent(id!); notify("削除しました。"); nav("/calendar"); } catch (e) { handleError(e); }
  };

  if (loading) return <Loading />;

  return (
    <>
      <div className="page-header"><h1>{isNew ? "予定を追加" : "予定を編集"}</h1></div>
      {error && <p className="err" role="alert" style={{ marginBottom: "var(--sp-3)" }}>{error}</p>}

      <div className="stack" style={{ maxWidth: "36rem" }}>
        <Field label="タイトル" htmlFor="title">
          <TextField id="title" maxLength={200} value={title} onChange={(e) => setTitle(e.target.value)} data-testid="event-title" />
        </Field>
        <Field label="日時" htmlFor="date">
          <TextField id="date" type="datetime-local" value={dateLocal} onChange={(e) => setDateLocal(e.target.value)} data-testid="event-date" />
        </Field>
        <Field label="場所（任意）" htmlFor="loc">
          <TextField id="loc" maxLength={200} value={location} onChange={(e) => setLocation(e.target.value)} data-testid="event-location" />
        </Field>
        <Field label="メモ（任意）" htmlFor="desc">
          <TextArea id="desc" value={description} onChange={(e) => setDescription(e.target.value)} data-testid="event-desc" />
        </Field>
        <Field label="公開状態" htmlFor="st">
          <Select id="st" value={status} onChange={(e) => setStatus(e.target.value as "draft" | "published")} data-testid="event-status">
            <option value="published">公開中</option>
            <option value="draft">下書き</option>
          </Select>
        </Field>
      </div>

      <div className="form-actions">
        <Button disabled={saving} onClick={save} data-testid="event-save">保存する</Button>
        {!isNew && <Button variant="danger" disabled={saving} onClick={() => setConfirmDel(true)} data-testid="event-delete">削除</Button>}
      </div>

      <ConfirmDialog open={confirmDel} title="この予定を削除しますか？" onConfirm={doDelete} onCancel={() => setConfirmDel(false)} />
    </>
  );
}
