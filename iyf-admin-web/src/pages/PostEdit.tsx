// ブログ作成/編集（TipTap・下書き保存/公開/削除）。オーナー制はサーバー権威（403/409をUIに反映）。
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { createPost, deletePost, getPostAdmin, setPostStatus, updatePost } from "../api/client";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { RichTextEditor } from "../components/RichTextEditor";
import { useToast } from "../components/Toast";
import { Button, Field, Loading, TextField } from "../components/ui";
import type { PostInput } from "../api/types";

export function PostEdit() {
  const { id } = useParams();
  const isNew = !id;
  const nav = useNavigate();
  const { notify } = useToast();

  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("");
  const [body, setBody] = useState("<p></p>");
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [confirmDel, setConfirmDel] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isNew) return;
    getPostAdmin(id!)
      .then((p) => { setTitle(p.title); setCategory(p.category ?? ""); setBody(p.body || "<p></p>"); })
      .catch((e) => setError(e instanceof Error ? e.message : "読み込みに失敗しました。"))
      .finally(() => setLoading(false));
  }, [id, isNew]);

  const buildInput = (status: "draft" | "published"): PostInput => ({
    title: title.trim(), body, category: category.trim() || null, status,
  });

  const handleError = (e: unknown) => {
    const msg = e instanceof Error ? e.message : "保存に失敗しました。";
    setError(msg);
    notify(msg, "error");
    // 409（プロフィール未完了）はプロフィールへ誘導。
    if (e && typeof e === "object" && "status" in e && (e as { status: number }).status === 409) {
      nav("/profile");
    }
  };

  const save = async (status: "draft" | "published") => {
    setError(null);
    if (title.trim().length < 1) { setError("タイトルを入力してください。"); return; }
    if (status === "published" && !stripHtml(body)) { setError("公開するには本文が必要です。"); return; }
    setSaving(true);
    try {
      if (isNew) {
        const created = await createPost(buildInput(status));
        notify(status === "published" ? "公開しました。" : "下書きを保存しました。");
        nav(`/posts/${created.post_id}`);
      } else {
        await updatePost(id!, buildInput(status));
        notify("保存しました。");
      }
    } catch (e) { handleError(e); } finally { setSaving(false); }
  };

  const unpublish = async () => {
    setSaving(true);
    try { await setPostStatus(id!, "draft"); notify("下書きに戻しました（公開を取り下げ）。"); }
    catch (e) { handleError(e); } finally { setSaving(false); }
  };

  const doDelete = async () => {
    setConfirmDel(false);
    try { await deletePost(id!); notify("削除しました。"); nav("/posts"); }
    catch (e) { handleError(e); }
  };

  if (loading) return <Loading />;

  return (
    <>
      <div className="page-header"><h1>{isNew ? "ブログ作成" : "ブログ編集"}</h1></div>
      {error && <p className="err" role="alert" style={{ marginBottom: "var(--sp-3)" }}>{error}</p>}

      <div className="stack" style={{ maxWidth: "44rem" }}>
        <Field label="タイトル" htmlFor="title">
          <TextField id="title" maxLength={200} value={title} onChange={(e) => setTitle(e.target.value)} data-testid="post-title" />
        </Field>
        <Field label="カテゴリ（任意）" htmlFor="cat">
          <TextField id="cat" maxLength={60} value={category} onChange={(e) => setCategory(e.target.value)} data-testid="post-category" />
        </Field>
        <Field label="本文">
          <RichTextEditor value={body} onChange={setBody} />
        </Field>
      </div>

      <div className="form-actions">
        <Button variant="secondary" disabled={saving} onClick={() => save("draft")} data-testid="post-save-draft">下書き保存</Button>
        <Button disabled={saving} onClick={() => save("published")} data-testid="post-publish">公開する</Button>
        {!isNew && <Button variant="secondary" disabled={saving} onClick={unpublish} data-testid="post-unpublish">公開を取り下げ</Button>}
        {!isNew && <Button variant="danger" disabled={saving} onClick={() => setConfirmDel(true)} data-testid="post-delete">削除</Button>}
      </div>

      <ConfirmDialog open={confirmDel} title="この記事を削除しますか？" message="削除すると元に戻せません。" onConfirm={doDelete} onCancel={() => setConfirmDel(false)} />
    </>
  );
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, "").replace(/&nbsp;/g, " ").trim();
}
