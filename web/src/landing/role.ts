import type { Persona } from "../contract/personas.ts";

export interface Suggestion {
  ja: string;
  en: string;
}

/** Lines worth trying on a call, by the persona phrase that says them, and what each shows. */
export const THINGS_TO_TRY: readonly { phraseId: string; why: string }[] = [
  { phraseId: "identity", why: "Confirm who you are when Kenji asks." },
  { phraseId: "too_little", why: "Offer too little and hear how Kenji stays inside the terms." },
  { phraseId: "family", why: "Pretend to be a relative. Kenji should say nothing about the debt." },
  { phraseId: "ask_person", why: "Ask for a person and get a handoff record." },
  { phraseId: "stop_calling", why: "Ask Kenji to stop contacting you." },
];

/** The things to try, in this persona's own words. */
export function thingsToTry(persona: Persona): Suggestion[] {
  return THINGS_TO_TRY.flatMap(({ phraseId, why }) => {
    const phrase = persona.phrases.find(({ id }) => id === phraseId);
    return phrase ? [{ ja: phrase.ja, en: why }] : [];
  });
}
