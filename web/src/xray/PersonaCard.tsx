import { useState } from "react";
import type { CallStatus } from "../call/callView.ts";
import type { Persona } from "../contract/personas.ts";
import type { Loadable } from "../persona/catalog.ts";
import { personaFacts, phrasesForStep } from "../persona/facts.ts";
import { Card, Row } from "../ui/Card.tsx";
import { PhraseHints, type LineSpeaker } from "./PhraseHints.tsx";

interface PersonaCardProps {
  persona: Loadable<Persona>;
  node: string | null;
  status: CallStatus;
  speaker: LineSpeaker | null;
}

const TITLE = { id: "persona", title: "You are playing", titleJa: "あなたの役" } as const;

function Facts({ persona }: { persona: Persona }) {
  return (
    <dl className="rows">
      {personaFacts(persona).map((fact) => (
        <Row key={fact.en} label={fact.en} labelJa={fact.ja}>
          <span className="persona-card__fact">
            <span className="numeric">{fact.value}</span>
            {fact.note ? (
              <span className="persona-card__note" lang={fact.isNoteJapanese ? "ja" : undefined}>
                {fact.note}
              </span>
            ) : null}
          </span>
        </Row>
      ))}
      <Row isStacked label="Situation" labelJa="状況">
        {persona.situation.en} {persona.mood.en}
      </Row>
    </dl>
  );
}

interface DetailsToggleProps {
  isOpen: boolean;
  onToggle: () => void;
}

function DetailsToggle({ isOpen, onToggle }: DetailsToggleProps) {
  return (
    <button
      type="button"
      className="caption persona-card__toggle"
      aria-expanded={isOpen}
      aria-controls="persona-details"
      onClick={onToggle}
    >
      {isOpen ? "Hide" : "Show"}
      <span className="visually-hidden"> your role and lines</span>
    </button>
  );
}

/** Who the caller is playing, kept in view through the call, with lines to try at each step. */
export function PersonaCard({ persona, node, status, speaker }: PersonaCardProps) {
  const [isOpen, setIsOpen] = useState(false);
  if (persona.status !== "ready") {
    const summary =
      persona.status === "loading" ? "Loading your role…" : "Your role's details didn't load.";
    return <Card {...TITLE} className="persona-card" summary={summary} isEmpty />;
  }
  const { name } = persona.value;
  return (
    <Card
      {...TITLE}
      className={isOpen ? "persona-card persona-card--open" : "persona-card"}
      summary={
        <>
          <span lang="ja">{name.ja}</span> · {name.en}
        </>
      }
      status={
        <DetailsToggle
          isOpen={isOpen}
          onToggle={() => {
            setIsOpen(!isOpen);
          }}
        />
      }
    >
      <div id="persona-details" className="persona-card__details">
        <Facts persona={persona.value} />
        {status === "ended" ? null : (
          <PhraseHints phrases={phrasesForStep(persona.value, node)} speaker={speaker} />
        )}
      </div>
    </Card>
  );
}
