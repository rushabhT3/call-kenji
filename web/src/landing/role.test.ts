import { describe, expect, it } from "vitest";
import catalog from "../../public/personas.json";
import { parsePersonaCatalog } from "../persona/catalog.ts";
import { THINGS_TO_TRY, thingsToTry } from "./role.ts";

describe("role card", () => {
  it("reads the catalog the page is served", () => {
    expect(() => parsePersonaCatalog(catalog)).not.toThrow();
  });

  it("offers every thing to try in each persona's own words", () => {
    for (const persona of parsePersonaCatalog(catalog).personas) {
      expect(thingsToTry(persona), persona.id).toHaveLength(THINGS_TO_TRY.length);
    }
  });

  it("quotes the persona's line for each suggestion", () => {
    const sato = parsePersonaCatalog(catalog).personas.find(({ id }) => id === "sato");
    if (sato === undefined) {
      throw new Error("the catalog has no sato persona");
    }

    expect(thingsToTry(sato)[0]).toEqual({
      ja: "佐藤ゆうきです。生年月日は、平成2年7月14日です。",
      en: "Confirm who you are when Kenji asks.",
    });
  });
});
