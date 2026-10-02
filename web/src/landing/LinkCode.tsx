interface LinkCodeProps {
  code: string | null;
}

export function LinkCode({ code }: LinkCodeProps) {
  if (code === null) {
    return (
      <p className="link-code__pending">
        Your private code appears here once this page is connected.
      </p>
    );
  }
  const digits = code.split("");
  return (
    <div className="link-code">
      <p className="caption link-code__label">
        Your code · <span lang="ja">認証コード</span>
      </p>
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
