import { describe, expect, it } from "vitest";
import type { Persona, PersonaPhrase } from "../contract/personas.ts";
import { personaFacts, phrasesForStep } from "./facts.ts";

const phrase = (id: string, steps: string[]): PersonaPhrase => ({
  id,
  steps,
  label: id,
  ja: id,
  en: id,
  clip: `/phrases/tanaka/${id}.m4a`,
});

const TANAKA: Persona = {
  id: "tanaka",
  name: { ja: "田中けんた", kana: "たなかけんた", en: "Kenta Tanaka" },
  birth: { iso: "1985-03-02", ja: "昭和60年3月2日" },
  account_suffix: "4410",
  balance_yen: 52000,
  overdue_since: "2026-08-31",
  situation: { en: "", ja: "" },
  mood: { en: "", ja: "" },
  phrases: [
    phrase("identity", ["greeting", "verify_identity"]),
    phrase("story", ["state_balance", "listen"]),
    phrase("too_little", ["state_balance", "listen", "negotiate"]),
    phrase("confirm", ["read_back"]),
  ],
};

describe("personaFacts", () => {
  it("gives the birth date in both forms, the account ending and what is overdue since when", () => {
    expect(personaFacts(TANAKA).map(({ value, note }) => [value, note])).toEqual([
      ["1985-03-02", "昭和60年3月2日"],
      ["4410", ""],
      ["¥52,000", "since 31 Aug"],
    ]);
  });
});

describe("phrasesForStep", () => {
  it("offers the lines that fit the step Kenji is at, in the persona's order", () => {
    expect(phrasesForStep(TANAKA, "listen").map(({ id }) => id)).toEqual(["story", "too_little"]);
  });

  it("offers nothing at a step no line fits", () => {
    expect(phrasesForStep(TANAKA, "close")).toEqual([]);
  });

  it("offers nothing before Kenji has reached a step", () => {
    expect(phrasesForStep(TANAKA, null)).toEqual([]);
  });
});
