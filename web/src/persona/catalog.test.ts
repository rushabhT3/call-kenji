import { describe, expect, it } from "vitest";
import type { Persona, PersonaCatalog } from "../contract/personas.ts";
import {
  FALLBACK_PERSONA_ID,
  chosenPersona,
  parsePersonaCatalog,
  personaIdForCall,
  personaOnCall,
  surprisePersonaId,
} from "./catalog.ts";

const persona = (id: string): Persona => ({
  id,
  name: { ja: id, kana: id, en: id },
  birth: { iso: "1990-07-14", ja: "平成2年7月14日" },
  account_suffix: "7731",
  balance_yen: 35000,
  overdue_since: "2026-09-30",
  situation: { en: "", ja: "" },
  mood: { en: "", ja: "" },
  phrases: [],
});

const CATALOG: PersonaCatalog = {
  default: "sato",
  personas: [persona("sato"), persona("tanaka"), persona("suzuki")],
};

describe("parsePersonaCatalog", () => {
  it("accepts a catalog whose default is one of its personas", () => {
    expect(parsePersonaCatalog(CATALOG)).toEqual(CATALOG);
  });

  it("rejects a default that names no persona", () => {
    expect(() => parsePersonaCatalog({ ...CATALOG, default: "nobody" })).toThrow(/nobody/);
  });

  it("rejects an empty or malformed catalog", () => {
    expect(() => parsePersonaCatalog({ default: "sato", personas: [] })).toThrow();
    expect(() => parsePersonaCatalog({ default: "sato", personas: [{ id: 1 }] })).toThrow();
    expect(() => parsePersonaCatalog(null)).toThrow();
  });
});

describe("chosenPersona", () => {
  it("is the persona the visitor chose", () => {
    expect(chosenPersona(CATALOG, "tanaka").id).toBe("tanaka");
  });

  it("falls back to the default for no choice or a choice the catalog no longer has", () => {
    expect(chosenPersona(CATALOG, null).id).toBe("sato");
    expect(chosenPersona(CATALOG, "retired").id).toBe("sato");
  });
});

describe("surprisePersonaId", () => {
  it("never picks the persona already chosen", () => {
    const picks = [0, 0.4, 0.99].map((value) => surprisePersonaId(CATALOG, "sato", () => value));

    expect(picks).toEqual(["tanaka", "tanaka", "suzuki"]);
  });

  it("stays in range when the random source returns its upper bound", () => {
    expect(surprisePersonaId(CATALOG, "tanaka", () => 1)).toBe("suzuki");
  });

  it("keeps the only persona of a one-persona catalog", () => {
    const single = { default: "sato", personas: [persona("sato")] };

    expect(surprisePersonaId(single, "sato", () => 0.5)).toBe("sato");
  });
});

describe("personaOnCall", () => {
  it("shows the persona the server says the call plays", () => {
    expect(personaOnCall(CATALOG, { startedId: "suzuki", chosenId: "tanaka" }).id).toBe("suzuki");
  });

  it("shows this tab's choice when the server does not say", () => {
    expect(personaOnCall(CATALOG, { startedId: null, chosenId: "tanaka" }).id).toBe("tanaka");
  });

  it("shows the default for a replay, which has no persona and ignores this tab's choice", () => {
    expect(personaOnCall(CATALOG, { startedId: null, chosenId: null }).id).toBe("sato");
  });

  it("ignores a persona id the catalog does not have", () => {
    expect(personaOnCall(CATALOG, { startedId: "ghost", chosenId: "tanaka" }).id).toBe("tanaka");
  });
});

describe("personaIdForCall", () => {
  it("asks for the chosen persona once the catalog has loaded", () => {
    expect(personaIdForCall({ status: "ready", value: CATALOG }, "suzuki")).toBe("suzuki");
  });

  it("asks for the fallback persona while the catalog is loading or after it failed", () => {
    expect(personaIdForCall({ status: "loading" }, "suzuki")).toBe(FALLBACK_PERSONA_ID);
    expect(personaIdForCall({ status: "failed" }, "suzuki")).toBe(FALLBACK_PERSONA_ID);
  });
});
