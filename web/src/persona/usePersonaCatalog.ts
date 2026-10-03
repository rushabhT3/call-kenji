import { useCallback, useEffect, useState } from "react";
import { PERSONAS_URL, type PersonaCatalog } from "../contract/personas.ts";
import { parsePersonaCatalog, type Loadable } from "./catalog.ts";

export interface PersonaCatalogLoad {
  catalog: Loadable<PersonaCatalog>;
  retry: () => void;
}

async function fetchCatalog(): Promise<PersonaCatalog> {
  const response = await fetch(PERSONAS_URL);
  if (!response.ok) {
    throw new Error(`persona catalog unavailable (${String(response.status)})`);
  }
  return parsePersonaCatalog(await response.json());
}

/** The fictional people a caller can play, loaded once from the static catalog. */
export function usePersonaCatalog(): PersonaCatalogLoad {
  const [catalog, setCatalog] = useState<Loadable<PersonaCatalog>>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let isCancelled = false;
    const load = async () => {
      try {
        const value = await fetchCatalog();
        if (!isCancelled) {
          setCatalog({ status: "ready", value });
        }
      } catch {
        if (!isCancelled) {
          setCatalog({ status: "failed" });
        }
      }
    };
    void load();
    return () => {
      isCancelled = true;
    };
  }, [attempt]);

  const retry = useCallback(() => {
    setCatalog({ status: "loading" });
    setAttempt((previous) => previous + 1);
  }, []);

  return { catalog, retry };
}
