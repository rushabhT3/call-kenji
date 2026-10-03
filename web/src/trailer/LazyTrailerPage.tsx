import { lazy } from "react";

/** The trailer page in its own chunk, so no other page loads it. */
export const LazyTrailerPage = lazy(async () => {
  const { TrailerPage } = await import("./TrailerPage.tsx");
  return { default: TrailerPage };
});
