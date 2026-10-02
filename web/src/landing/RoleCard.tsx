import { formatCount } from "../format.ts";
import { ROLE, THINGS_TO_TRY } from "./role.ts";

function Facts() {
  const facts = [
    { en: "Date of birth", ja: "生年月日", value: ROLE.dateOfBirth, note: ROLE.dateOfBirthJa },
    { en: "Account ending", ja: "口座番号末尾", value: ROLE.accountSuffix, note: null },
    {
      en: "Overdue",
      ja: "未納額",
      value: `¥${formatCount(ROLE.balanceYen)}`,
      note: "since 30 Sep",
    },
  ];
  return (
    <dl className="role__facts">
      {facts.map((fact) => (
        <div key={fact.en} className="role__fact">
          <dt className="caption">
            {fact.en} · <span lang="ja">{fact.ja}</span>
          </dt>
          <dd className="role__value numeric">
            {fact.value}
            {fact.note ? <span className="role__note">{fact.note}</span> : null}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export function RoleCard() {
  return (
    <section className="role" aria-labelledby="role-title">
      <p className="caption">
        Your role · <span lang="ja">あなたの役</span>
      </p>
      <h2 id="role-title" className="role__name">
        <span lang="ja">{ROLE.nameJa}</span>
        <span className="role__name-en">{ROLE.nameEn}</span>
      </h2>
      <Facts />
      <h3 className="caption role__try-title">Things to try</h3>
      <ul className="role__try">
        {THINGS_TO_TRY.map((suggestion) => (
          <li key={suggestion.ja}>
            <span lang="ja">「{suggestion.ja}」</span>
            <span className="role__try-en">{suggestion.en}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
