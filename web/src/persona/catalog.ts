import type { Persona, PersonaCatalog } from "../contract/personas.ts";

/** Who a call plays when the page could not load the catalog. */
export const FALLBACK_PERSONA_ID = "sato";

export type Loadable<T> =
  { status: "loading" } | { status: "failed" } | { status: "ready"; value: T };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isPersona(value: unknown): value is Persona {
  return isRecord(value) && typeof value.id === "string" && Array.isArray(value.phrases);
}

/** The catalog as served at /personas.json, or an error naming what is wrong with it. */
export function parsePersonaCatalog(raw: unknown): PersonaCatalog {
  if (!isRecord(raw) || !Array.isArray(raw.personas) || typeof raw.default !== "string") {
    throw new Error("persona catalog needs a default id and a list of personas");
  }
  const personas: unknown[] = raw.personas;
  if (personas.length === 0 || !personas.every(isPersona)) {
    throw new Error("persona catalog has no personas, or one without an id and phrases");
  }
  const defaultId = raw.default;
  if (!personas.some((persona) => persona.id === defaultId)) {
    throw new Error(`persona catalog default "${defaultId}" is not one of its personas`);
  }
  return { default: defaultId, personas };
}

export function findPersona(catalog: PersonaCatalog, id: string | null): Persona | null {
  return catalog.personas.find((persona) => persona.id === id) ?? null;
}

function defaultPersona(catalog: PersonaCatalog): Persona {
  const persona = findPersona(catalog, catalog.default) ?? catalog.personas[0];
  if (persona === undefined) {
    throw new Error("persona catalog is empty");
  }
  return persona;
}

/** The persona the visitor chose, or the catalog's default when that choice is not in it. */
export function chosenPersona(catalog: PersonaCatalog, chosenId: string | null): Persona {
  return findPersona(catalog, chosenId) ?? defaultPersona(catalog);
}

/** A persona other than the current one, picked by `random` (a number in [0, 1)). */
export function surprisePersonaId(
  catalog: PersonaCatalog,
  currentId: string,
  random: () => number,
): string {
  const others = catalog.personas.filter((persona) => persona.id !== currentId);
  const candidates = others.length > 0 ? others : catalog.personas;
  const index = Math.min(candidates.length - 1, Math.floor(random() * candidates.length));
  return candidates[index]?.id ?? currentId;
}

export interface CallPersonaSources {
  /** The persona the server says this call plays, from CallStarted. */
  startedId: string | null;
  /** The persona chosen on this tab; null when the choice does not apply, as in the demo. */
  chosenId: string | null;
}

/** The persona a call shows: the server's word first, then this tab's choice, then the default. */
export function personaOnCall(catalog: PersonaCatalog, sources: CallPersonaSources): Persona {
  return findPersona(catalog, sources.startedId) ?? chosenPersona(catalog, sources.chosenId);
}

/** The persona a call shows, once the catalog has loaded. */
export function personaShownOnCall(
  catalog: Loadable<PersonaCatalog>,
  sources: CallPersonaSources,
): Loadable<Persona> {
  return catalog.status === "ready"
    ? { status: "ready", value: personaOnCall(catalog.value, sources) }
    : catalog;
}

/** The persona id a browser call asks the server for. */
export function personaIdForCall(
  catalog: Loadable<PersonaCatalog>,
  chosenId: string | null,
): string {
  return catalog.status === "ready"
    ? chosenPersona(catalog.value, chosenId).id
    : FALLBACK_PERSONA_ID;
}
