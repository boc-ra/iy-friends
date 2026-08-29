const history = [
  { year: "昭和50年代初期", text: "自治会の青少年育成の一環事業として、各地区でポートボールチームが発足。" },
  { year: "昭和50年（1975年）", text: "上郷新大船ポートボールクラブ結成（上郷連合に所属）。" },
  { year: "昭和52年（1977年）", text: "フローラ桂台ポートボールクラブ結成（本郷中央地区に所属）。" },
  { year: "昭和60年（1985年）", text: "上郷新大船ポートボールクラブが「犬山ミニバスケットボール」へ名称変更。" },
  { year: "平成2年（1990年）", text: "フローラ桂台ポートボールクラブと上之ミニバスが合併し、「フローラ桂台ミニバス」へ名称変更。" },
  { year: "平成6年（1994年）", text: "フローラ桂台ミニバスと犬山ミニバスが合併。" },
  { year: "平成7年（1995年）", text: "上郷連合の上郷ミニバスが解散となり、選手の一部が入部。" },
  { year: "平成8年（1996年）", text: "「IYフレンズ」に名称変更。" },
  { year: "平成21年（2009年）3月", text: "栄区大会に男子チームが初参加。" },
  { year: "平成28年（2016年）4月", text: "「フレンズ」に名称変更。" },
];

export function About() {
  return (
    <>
      <div className="page-head">
        <div className="container">
          <h1>クラブ紹介</h1>
          <p className="lead">IYフレンズのあゆみ。</p>
        </div>
      </div>
      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container narrow">
          <h2 style={{ marginBottom: "var(--sp-8)" }}>あゆみ</h2>
          <ol className="timeline">
            {history.map((h) => (
              <li key={h.year} className="tl-item">
                <div className="tl-year">{h.year}</div>
                <div className="tl-text">{h.text}</div>
              </li>
            ))}
          </ol>
        </div>
      </section>
    </>
  );
}
