import { useCallback, useState } from "react";
import type { Persona, PersonaCatalog } from "../contract/personas.ts";
import { chosenPersona, surprisePersonaId, type Loadable } from "./catalog.ts";
import { readChosenPersonaId, rememberChosenPersonaId } from "./choiceStorage.ts";

export interface PersonaChoice {
  /** The id this tab chose, as remembered; it may name a persona the catalog no longer has. */
  chosenId: string | null;
  /** The persona the visitor will play, once the catalog has loaded. */
  chosen: Persona | null;
  choose: (id: string) => void;
  surprise: () => void;
}

export function usePersonaChoice(catalog: Loadable<PersonaCatalog>): PersonaChoice {
  const [chosenId, setChosenId] = useState<string | null>(() => readChosenPersonaId());
  const chosen = catalog.status === "ready" ? chosenPersona(catalog.value, chosenId) : null;

  const choose = useCallback((id: string) => {
    setChosenId(id);
    rememberChosenPersonaId(id);
  }, []);

  const surprise = useCallback(() => {
    if (catalog.status === "ready" && chosen !== null) {
      choose(surprisePersonaId(catalog.value, chosen.id, Math.random));
    }
  }, [catalog, chosen, choose]);

  return { chosenId, chosen, choose, surprise };
}
