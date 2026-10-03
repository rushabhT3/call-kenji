import "@fontsource/bebas-neue/400.css";
import "@fontsource/oswald/400.css";
import "@fontsource/oswald/500.css";
import "@fontsource/permanent-marker/400.css";
import "@fontsource/yusei-magic/400.css";
import { useState } from "react";
import { continueRender, delayRender } from "remotion";
import timeline from "./timeline.json";

const JAPANESE = Object.values(timeline.voice)
  .map((line) => line.ja)
  .join("")
  .concat("ケンジに電話日本語で");

const REQUESTS: [string, string][] = [
  ["100px 'Bebas Neue'", "EVERY PHONE CALL HAS A SILENCE 0123456789%/–.s"],
  ["40px Oswald", "Thank you for calling. I'm Kenji 0123456789¥,"],
  ["500 40px Oswald", "call-kenji.call-kenji-web.workers.dev"],
  ["100px 'Permanent Marker'", "CALL KENJI! Built by Rushabh Trivedi"],
  ["60px 'Yusei Magic'", JAPANESE],
];

/** Holds every frame until the faces it needs are loaded, so no frame renders in a fallback font. */
export function useFontsReady(): void {
  useState(() => {
    const handle = delayRender("Loading trailer fonts");
    void Promise.all(REQUESTS.map(([font, text]) => document.fonts.load(font, text))).then(() => {
      continueRender(handle);
    });
    return handle;
  });
}
