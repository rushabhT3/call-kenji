import type { ReactNode } from "react";
import { CallStop } from "./CallStop.tsx";
import { KenjiStop } from "./KenjiStop.tsx";
import { ProblemStop } from "./ProblemStop.tsx";
import { ProofStop } from "./ProofStop.tsx";
import { RulesStop } from "./RulesStop.tsx";
import { SpeedStop } from "./SpeedStop.tsx";
import { StackStop } from "./StackStop.tsx";
import type { StopId } from "./stops.ts";
import { TurnsStop } from "./TurnsStop.tsx";
import { XrayStop } from "./XrayStop.tsx";

const CONTENT: Record<StopId, ReactNode> = {
  problem: <ProblemStop />,
  kenji: <KenjiStop />,
  xray: <XrayStop />,
  speed: <SpeedStop />,
  turns: <TurnsStop />,
  rules: <RulesStop />,
  stack: <StackStop />,
  proof: <ProofStop />,
  call: <CallStop />,
};

export function StopContent({ id }: { id: StopId }) {
  return CONTENT[id];
}
