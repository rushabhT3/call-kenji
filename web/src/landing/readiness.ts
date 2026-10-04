import type { FeedStatus } from "../call/viewerFeed.ts";

/** Whether Kenji's server can take a call yet: it sleeps when idle and wakes for the page. */
export type ServerReadiness = "waking" | "ready" | "unreachable";

export function serverReadiness(viewerId: string | null, feedStatus: FeedStatus): ServerReadiness {
  if (viewerId !== null) {
    return "ready";
  }
  return feedStatus === "lost" ? "unreachable" : "waking";
}
