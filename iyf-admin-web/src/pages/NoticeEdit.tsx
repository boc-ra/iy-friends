// お知らせ作成/編集（ブログ同型・カテゴリなし）。
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { createNotice, deleteNotice, getNoticeAdmin, setNoticeStatus, updateNotice } from "../api/client";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { RichTextEditor } from "../components/RichTextEditor";
import { useToast } from "../components/Toast";
import { Button, Field, Loading, TextField } from "../components/ui";
import type { NoticeInput } from "../api/types";

export function NoticeEdit() {
  const { id } = useParams();
  const isNew = !id;
  const nav = useNavigate();
  const { notify } = useToast();

  const [title, setTitle] = useState("");
  const [body, setBody] = useState("<p></p>");
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [confirmDel, setConfirmDel] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isNew) return;
    getNoticeAdmin(id!)
      .then((n) => { setTitle(n.title); setBody(n.body || "<p></p>"); })
      .catch((e) => setError(e instanceof Error ? e.message : "読み込みに失敗しました。"))
      .finally(() => setLoading(false));
  }, [id, isNew]);

  const input = (status: "draft" | "published"): NoticeInput => ({ title: title.trim(), body, status });

  const handleError = (e: unknown) => {
    const msg = e instanceof Error ? e.message : "保存に失敗しました。";
    setError(msg); notify(msg, "error");
    if (e && typeof e === "object" && "status" in e && (e as { status: number }).status === 409) nav("/profile");
  };

  const save = async (status: "draft" | "published") => {
    setError(null);
    if (title.trim().length < 1) { setError("タイトルを入力してください。"); return; }
    if (status === "published" && !body.replace(/<[^>]*>/g, "").trim()) { setError("公開するには本文が必要です。"); return; }
    setSaving(true);
    try {
      if (isNew) { const c = await createNotice(input(status)); notify(status === "published" ? "公開しました。" : "下書きを保存しました。"); nav(`/notices/${c.notice_id}`); }
      else { await updateNotice(id!, input(status)); notify("保存しました。"); }
    } catch (e) { handleError(e); } finally { setSaving(false); }
  };

  const unpublish = async () => {
    setSaving(true);
    try { await setNoticeStatus(id!, "draft"); notify("下書きに戻しました。"); }
    catch (e) { handleError(e); } finally { setSaving(false); }
  };

  const doDelete = async () => {
    setConfirmDel(false);
    try { await deleteNotice(id!); notify("削除しました。"); nav("/notices"); } catch (e) { handleError(e); }
  };

  if (loading) return <Loading />;

  return (
    <>
      <div className="page-header"><h1>{isNew ? "お知らせ作成" : "お知らせ編集"}</h1></div>
      {error && <p className="err" role="alert" style={{ marginBottom: "var(--sp-3)" }}>{error}</p>}

      <div className="stack" style={{ maxWidth: "44rem" }}>
        <Field label="タイトル" htmlFor="title">
          <TextField id="title" maxLength={200} value={title} onChange={(e) => setTitle(e.target.value)} data-testid="notice-title" />
        </Field>
        <Field label="本文">
          <RichTextEditor value={body} onChange={setBody} />
        </Field>
      </div>

      <div className="form-actions">
        <Button variant="secondary" disabled={saving} onClick={() => save("draft")} data-testid="notice-save-draft">下書き保存</Button>
        <Button disabled={saving} onClick={() => save("published")} data-testid="notice-publish">公開する</Button>
        {!isNew && <Button variant="secondary" disabled={saving} onClick={unpublish}>公開を取り下げ</Button>}
        {!isNew && <Button variant="danger" disabled={saving} onClick={() => setConfirmDel(true)} data-testid="notice-delete">削除</Button>}
      </div>

      <ConfirmDialog open={confirmDel} title="このお知らせを削除しますか？" message="削除すると元に戻せません。" onConfirm={doDelete} onCancel={() => setConfirmDel(false)} />
    </>
  );
}
