const STORAGE_KEY = "call-kenji:persona";

type StorageSource = () => Storage;

// Reading window.localStorage itself throws where storage is blocked, so the access is deferred
// into the try blocks below.
const browserStorage: StorageSource = () => window.localStorage;

/** The persona this browser chose last time, or null when there is none or storage is blocked. */
export function readChosenPersonaId(storage: StorageSource = browserStorage): string | null {
  try {
    return storage().getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

/** Remembers the choice for next time; without storage the page simply forgets it. */
export function rememberChosenPersonaId(id: string, storage: StorageSource = browserStorage): void {
  try {
    storage().setItem(STORAGE_KEY, id);
  } catch {
    // Private windows and blocked site data refuse writes; the choice still holds on this tab.
  }
}
