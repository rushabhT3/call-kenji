const PROOFS = [
  {
    title: "Compliance is code, not a prompt.",
    text: "The model can only act through tools that check the terms, so it cannot agree to ¥3,000 a month however hard you push.",
  },
  {
    title: "Phone and browser, one agent.",
    text: "The same pipeline serves a browser call and a Twilio phone call, with the same rules and the same X-ray. The browser path is checked end to end; the phone path is built and tested, with a real phone call still to come.",
  },
  {
    title: "Costs are capped.",
    text: "Five minutes a call, a 60-minute daily pool for each channel, 25 calls a day per caller.",
  },
  {
    title: "Private by default.",
    text: "Calls are kept as text for 30 days and then deleted. Audio is never stored.",
  },
] as const;

function RefusalComic() {
  return (
    <figure className="refusal comic-panel comic-panel--red comic-reveal">
      <figcaption className="comic-label">From the recorded demo call</figcaption>
      <div className="bubble bubble--caller">
        <p className="comic-ja" lang="ja">
          今月はちょっと厳しくて、月3,000円なら払えます。
        </p>
        <p className="bubble__en">This month's tight, but I can pay 3,000 yen a month.</p>
      </div>
      <div className="bubble bubble--kenji">
        <p className="comic-ja" lang="ja">
          申し訳ございません。毎月3,000円ですと、お受けできる条件に届きません。毎月6,000円からでしたらお受けできますが、いかがでしょうか。
        </p>
        <p className="bubble__en">
          I'm sorry, ¥3,000 a month is below what we can accept. We can accept from ¥6,000 a month.
          Would that work for you?
        </p>
      </div>
    </figure>
  );
}

export function WhatItProves() {
  return (
    <section id="proves" className="showcase-section" aria-labelledby="proves-title">
      <div className="showcase__container showcase-split">
        <div>
          <p className="comic-label">For founders and CEOs</p>
          <h2 id="proves-title" className="showcase-heading">
            What it proves
          </h2>
          <p className="showcase-lead">
            Voice agents win or lose on three things a demo usually hides: turn-taking, compliance
            and latency. Kenji puts all three on screen.
          </p>
          <ul className="proof-list">
            {PROOFS.map((proof) => (
              <li key={proof.title} className="proof comic-reveal">
                <h3 className="proof__title">{proof.title}</h3>
                <p>{proof.text}</p>
              </li>
            ))}
          </ul>
        </div>
        <RefusalComic />
      </div>
    </section>
  );
}
