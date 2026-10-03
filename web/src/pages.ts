export const SHOWCASE_PATH = "/features";
export const PITCH_PATH = "/pitch";
export const TRAILER_PATH = "/trailer";

export type Page = "call" | "showcase" | "pitch" | "trailer";

const PAGE_PATHS: ReadonlyMap<string, Page> = new Map([
  [SHOWCASE_PATH, "showcase"],
  [PITCH_PATH, "pitch"],
  [TRAILER_PATH, "trailer"],
]);

/** The page an address shows; everything that is not a named page is the call page. */
export function pageForPath(pathname: string): Page {
  return PAGE_PATHS.get(pathname.replace(/\/+$/, "")) ?? "call";
}
