const ITEMS = [
  {
    title: "Turn",
    ja: "ターン",
    text: "When you speak over Kenji, he decides whether it was a polite はい or a real interruption.",
  },
  {
    title: "Strategist",
    ja: "戦略",
    text: "A second model reads each of your turns and suggests Kenji's next move, without slowing him down.",
  },
  {
    title: "Compliance",
    ja: "コンプライアンス",
    text: "Calling hours, the identity check, the payment terms and the disclosures, each shown as it holds.",
  },
  {
    title: "Latency",
    ja: "応答時間",
    text: "How long Kenji took to answer each time, against a 1,500 ms budget.",
  },
] as const;

export function Explainer() {
  return (
    <section id="how-to-read" className="explainer" aria-labelledby="explainer-title">
      <h2 id="explainer-title" className="explainer__title">
        How to read the X-ray
      </h2>
      <ul className="explainer__list">
        {ITEMS.map((item) => (
          <li key={item.title} className="explainer__item">
            <h3 className="caption">
              {item.title} · <span lang="ja">{item.ja}</span>
            </h3>
            <p>{item.text}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
