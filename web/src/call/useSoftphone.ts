import { useEffect, useState } from "react";

const SOFTPHONE_ENDPOINT = "/api/softphone";

async function fetchSoftphoneUrl(): Promise<string | null> {
  try {
    const response = await fetch(SOFTPHONE_ENDPOINT);
    if (!response.ok) {
      return null;
    }
    const body = (await response.json()) as { url?: unknown };
    return typeof body.url === "string" ? body.url : null;
  } catch {
    return null;
  }
}

/**
 * The dev softphone that calls the phone line through Twilio. The voice server names it only to
 * a browser on its own machine, so on the public site this stays null.
 */
export function useSoftphone(): string | null {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    let isCancelled = false;
    const load = async () => {
      const found = await fetchSoftphoneUrl();
      if (!isCancelled) {
        setUrl(found);
      }
    };
    void load();
    return () => {
      isCancelled = true;
    };
  }, []);
  return url;
}
