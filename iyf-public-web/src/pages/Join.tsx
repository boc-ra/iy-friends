import { Link } from "react-router-dom";

const faqs = [
  {
    q: "どんな子がやっていますか？",
    a: "現在の部員は、上郷小学校・庄戸小学校・桂台小学校・公田小学校・鎌倉女子大学初等部などの1年生〜6年生の男女です。OB・OGの選手も日々練習に参加しています。",
  },
  {
    q: "一年生でも幼稚園児でもできますか？",
    a: "みーんな大歓迎です。",
  },
  {
    q: "練習場所はどこですか？",
    a: "基本的には、上郷小学校の体育館です。",
  },
  {
    q: "運動神経はあまりよくないのですが…",
    a: "心配要りません。毎週練習すれば、必ずできるようになります。",
  },
  {
    q: "部費はいくらですか？",
    a: "スポーツ保険（年間）800円、部費（月）2,000円、合宿費（月／積立）2,000円です。（詳しくは「部費・規約」をご覧ください）",
  },
  {
    q: "見学できますか？",
    a: "いつでも見学に来てください。練習も体験できますので、体育館履き・水筒を忘れずにお持ちください。",
  },
];

export function Join() {
  return (
    <>
      <div className="page-head">
        <div className="container">
          <h1>メンバー募集</h1>
          <p className="lead">まずは体験から。お気軽にご参加ください。</p>
        </div>
      </div>
      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container narrow prose stack">
          <ul className="stack">
            {faqs.map((f) => (
              <li key={f.q} className="card entry-card">
                <h3>{f.q}</h3>
                <p className="muted">{f.a}</p>
              </li>
            ))}
          </ul>

          <div style={{ marginTop: "var(--sp-6)" }}>
            <Link to="/contact" className="btn" data-testid="join-cta">体験を申し込む</Link>
          </div>
        </div>
      </section>
    </>
  );
}
