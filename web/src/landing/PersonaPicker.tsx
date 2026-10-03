import type { Persona } from "../contract/personas.ts";
import { Button } from "../ui/Button.tsx";

interface PersonaPickerProps {
  personas: readonly Persona[];
  chosenId: string;
  onChoose: (id: string) => void;
  onSurprise: () => void;
}

interface PersonaOptionProps {
  persona: Persona;
  isChosen: boolean;
  onChoose: (id: string) => void;
}

function PersonaOption({ persona, isChosen, onChoose }: PersonaOptionProps) {
  const nameId = `persona-${persona.id}-name`;
  const aboutId = `persona-${persona.id}-about`;
  return (
    <label className={isChosen ? "persona-option persona-option--chosen" : "persona-option"}>
      <input
        type="radio"
        name="persona"
        value={persona.id}
        checked={isChosen}
        className="persona-option__input"
        aria-labelledby={nameId}
        aria-describedby={aboutId}
        onChange={() => {
          onChoose(persona.id);
        }}
      />
      <span className="persona-option__text">
        <span id={nameId} className="persona-option__name">
          <span lang="ja">{persona.name.ja}</span>
          <span className="persona-option__name-en">{persona.name.en}</span>
        </span>
        <span id={aboutId} className="persona-option__about">
          <span className="persona-option__situation">{persona.situation.en}</span>
          <span className="persona-option__mood">Mood: {persona.mood.en}</span>
        </span>
      </span>
    </label>
  );
}

/** The fictional people a visitor can play, one chosen at a time. */
export function PersonaPicker({ personas, chosenId, onChoose, onSurprise }: PersonaPickerProps) {
  return (
    <fieldset className="persona-picker">
      <legend className="caption persona-picker__legend">
        Choose who you play · <span lang="ja">役を選ぶ</span>
      </legend>
      <div className="persona-picker__options">
        {personas.map((persona) => (
          <PersonaOption
            key={persona.id}
            persona={persona}
            isChosen={persona.id === chosenId}
            onChoose={onChoose}
          />
        ))}
      </div>
      <Button size="sm" icon="shuffle" onClick={onSurprise}>
        Surprise me
      </Button>
    </fieldset>
  );
}
