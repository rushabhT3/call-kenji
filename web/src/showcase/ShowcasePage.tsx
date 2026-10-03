import "./showcase.css";
import "./diagrams.css";
import { useRef } from "react";
import { FinalCall } from "./FinalCall.tsx";
import { ShowcaseHero } from "./ShowcaseHero.tsx";
import { ShowcaseNav } from "./ShowcaseNav.tsx";
import { SpeedTricks } from "./SpeedTricks.tsx";
import { StackGrid } from "./StackGrid.tsx";
import { StatStrip } from "./StatStrip.tsx";
import { TurnTaking } from "./TurnTaking.tsx";
import { useShowcaseMotion } from "./useShowcaseMotion.ts";
import { WhatIDid } from "./WhatIDid.tsx";
import { WhatItProves } from "./WhatItProves.tsx";
import { XrayIsReal } from "./XrayIsReal.tsx";
import { XrayReveal } from "./XrayReveal.tsx";

export function ShowcasePage() {
  const rootRef = useRef<HTMLDivElement>(null);
  useShowcaseMotion(rootRef);
  return (
    <div ref={rootRef} className="showcase">
      <title>Call Kenji · Features and how it's built</title>
      <ShowcaseNav />
      <main>
        <ShowcaseHero />
        <StatStrip />
        <XrayReveal />
        <WhatItProves />
        <SpeedTricks />
        <TurnTaking />
        <XrayIsReal />
        <StackGrid />
        <WhatIDid />
        <FinalCall />
      </main>
    </div>
  );
}
