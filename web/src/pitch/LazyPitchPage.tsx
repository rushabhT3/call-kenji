import { lazy } from "react";

/** The zoomable pitch in its own chunk, so no other page loads it. */
export const LazyPitchPage = lazy(async () => {
  const { PitchPage } = await import("./PitchPage.tsx");
  return { default: PitchPage };
});
