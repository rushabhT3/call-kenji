import { PITCH_PATH, SHOWCASE_PATH } from "../pages.ts";

export const TRAILER_VIDEO = "/trailer/kenji-trailer.mp4";
export const TRAILER_POSTER = "/trailer/poster.webp";

export const TRAILER_DESCRIPTION =
  "A short trailer cut from a real recorded call: Kenji's own voice, real screenshots of the live X-ray, and how he starts answering in about 0.7 seconds on a model that needs 2 to 6.";

export interface TrailerLink {
  label: string;
  href: string;
  isPrimary: boolean;
}

export const TRAILER_LINKS: readonly TrailerLink[] = [
  { label: "Call Kenji", href: "/#call", isPrimary: true },
  { label: "Explore Kenji's Universe", href: PITCH_PATH, isPrimary: false },
  { label: "How it's built", href: SHOWCASE_PATH, isPrimary: false },
];

export const DEMO_LINK = { label: "Watch the demo call", href: "/?demo=1" } as const;
