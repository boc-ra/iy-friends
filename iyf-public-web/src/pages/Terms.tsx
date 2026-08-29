const fees = [
  { name: "部費", amount: "月 2,000円" },
  { name: "合宿積立金", amount: "月 2,000円" },
  { name: "スポーツ保険", amount: "年 800円" },
  { name: "チームTシャツ代", amount: "1枚 2,500円前後" },
];

const officerRoles = [
  "スポーツ保険の加入手続き（会計）",
  "連絡網・スケジュール表・名簿の作成（書記）",
  "毎月の部費袋の配布および集金（会計）",
  "親子大会・桂台祭り・合宿・クリスマス会・お別れ会などの準備",
  "試合等の連絡",
  "欠席者の連絡を受け付け、スタッフへ報告",
  "監督・コーチと保護者会との連絡役",
];

export function Terms() {
  return (
    <>
      <div className="page-head">
        <div className="container">
          <h1>部費・規約</h1>
          <p className="lead">入部にあたっての費用と、保護者会の役割について。</p>
        </div>
      </div>
      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container narrow stack">
          <h2>諸費用</h2>
          <div className="card" style={{ padding: "var(--sp-6)" }}>
            <ul className="fee-list">
              {fees.map((f) => (
                <li key={f.name}>
                  <span><strong>{f.name}</strong></span>
                  <span className="muted">{f.amount}</span>
                </li>
              ))}
            </ul>
            <p className="muted" style={{ marginTop: "var(--sp-4)" }}>
              試合用ユニフォーム（上）・ボールはお貸しします。ユニフォームパンツは買い取りとなります。<br />
              ＜参考実績＞合宿費：合宿積立金12ヶ月分より 24,000円
            </p>
          </div>

          <h2 style={{ marginTop: "var(--sp-8)" }}>役員（保護者会）の役割</h2>
          <div className="card" style={{ padding: "var(--sp-6)" }}>
            <ul className="role-list">
              {officerRoles.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          </div>

          <h2 style={{ marginTop: "var(--sp-8)" }}>個人情報の取り扱い</h2>
          <div className="card" style={{ padding: "var(--sp-6)" }}>
            <p className="muted" style={{ margin: 0 }}>お問い合わせでいただいた個人情報は、対応の目的にのみ利用します。</p>
          </div>
        </div>
      </section>
    </>
  );
}
