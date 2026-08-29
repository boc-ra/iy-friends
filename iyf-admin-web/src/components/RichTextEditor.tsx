// TipTap ベースの本文エディタ。出力 HTML はバックエンド allowlist に整合
// （p/strong/em/u/s/h2/h3/ul/ol/li/a/blockquote/code/hr）。
import Link from "@tiptap/extension-link";
import Underline from "@tiptap/extension-underline";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { useEffect } from "react";

interface Props {
  value: string;
  onChange: (html: string) => void;
}

function Btn({ cmd, active, label, testid }: { cmd: () => void; active: boolean; label: string; testid: string }) {
  return (
    <button type="button" className={active ? "on" : ""} onMouseDown={(e) => { e.preventDefault(); cmd(); }} aria-pressed={active} title={label} data-testid={testid}>
      {label}
    </button>
  );
}

export function RichTextEditor({ value, onChange }: Props) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({ heading: { levels: [2, 3] } }),
      Underline,
      Link.configure({ openOnClick: false, autolink: true }),
    ],
    content: value,
    onUpdate: ({ editor }) => onChange(editor.getHTML()),
  });

  // 外部から value が差し替わった場合（編集ロード）に同期。
  useEffect(() => {
    if (editor && value !== editor.getHTML()) {
      editor.commands.setContent(value, false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, editor]);

  if (!editor) return null;

  const setLink = () => {
    const prev = editor.getAttributes("link").href as string | undefined;
    const url = window.prompt("リンクURL", prev ?? "https://");
    if (url === null) return;
    if (url === "") editor.chain().focus().unsetLink().run();
    else editor.chain().focus().extendMarkRange("link").setLink({ href: url }).run();
  };

  return (
    <div className="editor" data-testid="rich-editor">
      <div className="toolbar">
        <Btn label="B" testid="rt-bold" active={editor.isActive("bold")} cmd={() => editor.chain().focus().toggleBold().run()} />
        <Btn label="I" testid="rt-italic" active={editor.isActive("italic")} cmd={() => editor.chain().focus().toggleItalic().run()} />
        <Btn label="U" testid="rt-underline" active={editor.isActive("underline")} cmd={() => editor.chain().focus().toggleUnderline().run()} />
        <Btn label="S" testid="rt-strike" active={editor.isActive("strike")} cmd={() => editor.chain().focus().toggleStrike().run()} />
        <Btn label="H2" testid="rt-h2" active={editor.isActive("heading", { level: 2 })} cmd={() => editor.chain().focus().toggleHeading({ level: 2 }).run()} />
        <Btn label="H3" testid="rt-h3" active={editor.isActive("heading", { level: 3 })} cmd={() => editor.chain().focus().toggleHeading({ level: 3 }).run()} />
        <Btn label="•" testid="rt-ul" active={editor.isActive("bulletList")} cmd={() => editor.chain().focus().toggleBulletList().run()} />
        <Btn label="1." testid="rt-ol" active={editor.isActive("orderedList")} cmd={() => editor.chain().focus().toggleOrderedList().run()} />
        <Btn label="❝" testid="rt-quote" active={editor.isActive("blockquote")} cmd={() => editor.chain().focus().toggleBlockquote().run()} />
        <Btn label="&lt;/&gt;" testid="rt-code" active={editor.isActive("code")} cmd={() => editor.chain().focus().toggleCode().run()} />
        <Btn label="🔗" testid="rt-link" active={editor.isActive("link")} cmd={setLink} />
        <Btn label="―" testid="rt-hr" active={false} cmd={() => editor.chain().focus().setHorizontalRule().run()} />
      </div>
      <EditorContent editor={editor} />
    </div>
  );
}
