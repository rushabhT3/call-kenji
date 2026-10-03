import { lazy } from "react";

/** The features page in its own chunk, so the call page never loads its animation or fonts. */
export const LazyShowcasePage = lazy(async () => {
  const { ShowcasePage } = await import("./ShowcasePage.tsx");
  return { default: ShowcasePage };
});
