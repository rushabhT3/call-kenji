import type { Persona, PersonaCatalog } from "../contract/personas.ts";
import type { Loadable } from "../persona/catalog.ts";
import { personaFacts } from "../persona/facts.ts";
import { Button } from "../ui/Button.tsx";
import { PersonaPicker } from "./PersonaPicker.tsx";
import { thingsToTry } from "./role.ts";

interface RoleCardProps {
  catalog: Loadable<PersonaCatalog>;
  /** The persona the visitor plays; null until the catalog has loaded. */
  chosen: Persona | null;
  onChoose: (id: string) => void;
  onSurprise: () => void;
  onRetry: () => void;
}

function Facts({ persona }: { persona: Persona }) {
  return (
    <dl className="role__facts">
      {personaFacts(persona).map((fact) => (
        <div key={fact.en} className="role__fact">
          <dt className="caption">
            {fact.en} · <span lang="ja">{fact.ja}</span>
          </dt>
          <dd className="role__value numeric">
            {fact.value}
            {fact.note ? (
              <span className="role__note" lang={fact.isNoteJapanese ? "ja" : undefined}>
                {fact.note}
              </span>
            ) : null}
          </dd>
        </div>
      ))}
    </dl>
  );
}

function Identity({ persona }: { persona: Persona }) {
  return (
    <>
      <h2 className="role__name" aria-live="polite">
        <span lang="ja">{persona.name.ja}</span>
        <span className="role__name-en">{persona.name.en}</span>
      </h2>
      <Facts persona={persona} />
      <h3 className="caption role__try-title">Things to try</h3>
      <ul className="role__try">
        {thingsToTry(persona).map((suggestion) => (
          <li key={suggestion.ja}>
            <span lang="ja">「{suggestion.ja}」</span>
            <span className="role__try-en">{suggestion.en}</span>
          </li>
        ))}
      </ul>
    </>
  );
}

function CatalogFailed({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="role__status" role="alert">
      <p>The roles didn&apos;t load. You can still call Kenji in the default role, or try again.</p>
      <Button size="sm" onClick={onRetry}>
        Try again
      </Button>
    </div>
  );
}

export function RoleCard({ catalog, chosen, onChoose, onSurprise, onRetry }: RoleCardProps) {
  return (
    <section className="role" aria-labelledby="role-caption">
      <p id="role-caption" className="caption">
        Your role · <span lang="ja">あなたの役</span>
      </p>
      {catalog.status === "loading" ? (
        <p className="role__status" role="status">
          Loading the people you can play…
        </p>
      ) : null}
      {catalog.status === "failed" ? <CatalogFailed onRetry={onRetry} /> : null}
      {catalog.status === "ready" && chosen ? (
        <>
          <PersonaPicker
            personas={catalog.value.personas}
            chosenId={chosen.id}
            onChoose={onChoose}
            onSurprise={onSurprise}
          />
          <Identity persona={chosen} />
        </>
      ) : null}
    </section>
  );
}
