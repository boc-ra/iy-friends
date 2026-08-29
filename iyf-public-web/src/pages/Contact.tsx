import { FormEvent, useState } from "react";
import { submitContact } from "../api/client";

type Errors = Partial<Record<"name" | "email" | "message", string>>;
type Status = "idle" | "sending" | "ok" | "error";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function Contact() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [status, setStatus] = useState<Status>("idle");

  function validate(): boolean {
    const e: Errors = {};
    if (!name.trim()) e.name = "お名前を入力してください。";
    if (!EMAIL_RE.test(email)) e.email = "メールアドレスの形式をご確認ください。";
    if (!message.trim()) e.message = "お問い合わせ内容を入力してください。";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function onSubmit(ev: FormEvent) {
    ev.preventDefault();
    if (status === "sending") return;          // 二重送信防止
    if (!validate()) return;
    setStatus("sending");
    try {
      await submitContact({ name: name.trim(), email: email.trim(), message: message.trim() });
      setStatus("ok");
      setName(""); setEmail(""); setMessage("");
    } catch {
      setStatus("error");
    }
  }

  return (
    <>
      <div className="page-head">
        <div className="container">
          <h1>お問い合わせ</h1>
          <p className="lead">体験・入会のご相談など、お気軽にどうぞ。</p>
        </div>
      </div>
      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container narrow">
          {status === "ok" && (
            <p className="form-banner ok" role="status" data-testid="contact-success">
              送信しました。お返事まで少々お待ちください。
            </p>
          )}
          {status === "error" && (
            <p className="form-banner err" role="alert" data-testid="contact-error">
              送信に失敗しました。時間をおいて再度お試しください。
            </p>
          )}

          <form className="stack" onSubmit={onSubmit} noValidate style={{ marginTop: "var(--sp-4)" }}>
            <div className="field">
              <label htmlFor="name">お名前</label>
              <input
                id="name" data-testid="contact-name" value={name}
                onChange={(e) => setName(e.target.value)} maxLength={100}
                aria-invalid={!!errors.name} autoComplete="name"
              />
              {errors.name && <span className="error-text">{errors.name}</span>}
            </div>

            <div className="field">
              <label htmlFor="email">メールアドレス</label>
              <input
                id="email" type="email" data-testid="contact-email" value={email}
                onChange={(e) => setEmail(e.target.value)} maxLength={254}
                aria-invalid={!!errors.email} autoComplete="email"
              />
              {errors.email && <span className="error-text">{errors.email}</span>}
            </div>

            <div className="field">
              <label htmlFor="message">お問い合わせ内容</label>
              <textarea
                id="message" data-testid="contact-message" value={message}
                onChange={(e) => setMessage(e.target.value)} rows={6} maxLength={5000}
                aria-invalid={!!errors.message}
              />
              {errors.message && <span className="error-text">{errors.message}</span>}
            </div>

            <div>
              <button type="submit" className="btn" data-testid="contact-submit" disabled={status === "sending"}>
                {status === "sending" ? "送信中…" : "送信する"}
              </button>
            </div>
          </form>
        </div>
      </section>
    </>
  );
}
