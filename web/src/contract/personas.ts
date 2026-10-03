/**
 * The fictional debtors a caller can play, as exported to /personas.json by
 * scripts/export_personas.py from content/personas.yaml.
 */

export interface PersonaText {
  en: string;
  ja: string;
}

/** A line the page offers at some steps of the call, and can speak for the caller. */
export interface PersonaPhrase {
  id: string;
  /** Flow steps where the line fits, such as "verify_identity" or "negotiate". */
  steps: string[];
  /** The button text, in English. */
  label: string;
  ja: string;
  en: string;
  /** The recorded clip of the line, spoken by the synthetic caller voice. */
  clip: string;
}

export interface Persona {
  id: string;
  name: { ja: string; kana: string; en: string };
  birth: { iso: string; ja: string };
  account_suffix: string;
  balance_yen: number;
  overdue_since: string;
  situation: PersonaText;
  mood: PersonaText;
  phrases: PersonaPhrase[];
}

export interface PersonaCatalog {
  default: string;
  personas: Persona[];
}

export const PERSONAS_URL = "/personas.json";
