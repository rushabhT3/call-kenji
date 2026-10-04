const CODE_LENGTH = 4;

interface LinkCodeProps {
  code: string | null;
}

function CodeLabel() {
  return (
    <p className="caption link-code__label">
      Your code · <span lang="ja">認証コード</span>
    </p>
  );
}

/** Empty cells hold the code's place while the server wakes, so nothing jumps when it lands. */
function PendingCode() {
  return (
    <div className="link-code">
      <CodeLabel />
      <div className="link-code__cells" aria-hidden="true">
        {Array.from({ length: CODE_LENGTH }, (_, index) => (
          <span key={index} className="link-code__cell link-code__cell--waiting" />
        ))}
      </div>
      <p className="link-code__pending">Getting your code…</p>
    </div>
  );
}

export function LinkCode({ code }: LinkCodeProps) {
  if (code === null) {
    return <PendingCode />;
  }
  const digits = code.split("");
  return (
    <div className="link-code">
      <CodeLabel />
      <div className="link-code__cells" role="group" aria-label={`Your code: ${digits.join(" ")}`}>
        {digits.map((digit, index) => (
          <span key={index} className="link-code__cell" aria-hidden="true">
            {digit}
          </span>
        ))}
      </div>
      <p className="link-code__help">
        Calling by phone? When Kenji asks, type these four digits on your keypad. Only this tab will
        show your call.
        <span lang="ja">ケンジがお願いしたら、電話のキーパッドで入力してください。</span>
      </p>
    </div>
  );
}
