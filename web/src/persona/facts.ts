import type { Persona, PersonaPhrase } from "../contract/personas.ts";
import { formatCount, formatDay } from "../format.ts";

export interface PersonaFact {
  en: string;
  ja: string;
  value: string;
  /** A second form of the value, or what it is measured from. */
  note: string;
  /** Whether the note is Japanese text. */
  isNoteJapanese: boolean;
}

/** What the caller may be asked to confirm, as the role card and the live card show it. */
export function personaFacts(persona: Persona): PersonaFact[] {
  return [
    {
      en: "Date of birth",
      ja: "生年月日",
      value: persona.birth.iso,
      note: persona.birth.ja,
      isNoteJapanese: true,
    },
    {
      en: "Account ending",
      ja: "口座番号末尾",
      value: persona.account_suffix,
      note: "",
      isNoteJapanese: false,
    },
    {
      en: "Overdue",
      ja: "未納額",
      value: `¥${formatCount(persona.balance_yen)}`,
      note: `since ${formatDay(persona.overdue_since)}`,
      isNoteJapanese: false,
    },
  ];
}

/** The persona's lines that fit the step Kenji is at; none before the first step. */
export function phrasesForStep(persona: Persona, node: string | null): PersonaPhrase[] {
  return node === null ? [] : persona.phrases.filter((phrase) => phrase.steps.includes(node));
}
