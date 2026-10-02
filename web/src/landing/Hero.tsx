export function Hero() {
  return (
    <section className="hero" aria-labelledby="hero-title">
      <p className="caption hero__eyebrow">
        A Japanese voice agent · <span lang="ja">音声エージェント</span>
      </p>
      <h1 id="hero-title" className="hero__title">
        Call Kenji.
        <br />
        <em>Watch him think.</em>
      </h1>
      <p className="hero__subtitle" lang="ja">
        AIのケンジが、架空の延滞のご相談をお受けします。
      </p>
      <p className="hero__lead">
        Kenji is an AI agent for a fictional Japanese debt servicer. You play the customer, on the
        phone or in your browser. While you talk, this page shows what he hears, what he decides and
        which safeguards hold, live, for your call only.
      </p>
    </section>
  );
}
