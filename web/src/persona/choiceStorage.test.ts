import { describe, expect, it } from "vitest";
import { readChosenPersonaId, rememberChosenPersonaId } from "./choiceStorage.ts";

function memoryStorage(): Storage {
  const items = new Map<string, string>();
  return {
    get length() {
      return items.size;
    },
    clear: () => {
      items.clear();
    },
    getItem: (key) => items.get(key) ?? null,
    key: (index) => [...items.keys()][index] ?? null,
    removeItem: (key) => {
      items.delete(key);
    },
    setItem: (key, value) => {
      items.set(key, value);
    },
  };
}

const blockedStorage = (): Storage => {
  throw new DOMException("The operation is insecure.", "SecurityError");
};

describe("chosen persona storage", () => {
  it("remembers the choice for the next visit", () => {
    const storage = memoryStorage();

    rememberChosenPersonaId("tanaka", () => storage);

    expect(readChosenPersonaId(() => storage)).toBe("tanaka");
  });

  it("has no choice on a first visit", () => {
    const storage = memoryStorage();

    expect(readChosenPersonaId(() => storage)).toBeNull();
  });

  it("works without storage when the browser blocks it", () => {
    expect(() => {
      rememberChosenPersonaId("tanaka", blockedStorage);
    }).not.toThrow();
    expect(readChosenPersonaId(blockedStorage)).toBeNull();
  });
});
