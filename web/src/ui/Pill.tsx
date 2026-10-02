import type { CheckStatus } from "../contract/events.ts";
import { Icon, type IconName } from "./Icon.tsx";

export type PillTone = CheckStatus | "info" | "caution";

const ICONS: Partial<Record<PillTone, IconName>> = {
  pass: "check",
  blocked: "cross",
  pending: "clock",
  caution: "clock",
};

const DEFAULT_LABELS: Record<CheckStatus, string> = {
  pass: "Pass",
  blocked: "Blocked",
  pending: "Pending",
};

interface PillProps {
  tone: PillTone;
  label?: string;
  context?: string;
}

export function Pill({ tone, label, context }: PillProps) {
  const icon = ICONS[tone];
  const text = label ?? (tone in DEFAULT_LABELS ? DEFAULT_LABELS[tone as CheckStatus] : "");
  return (
    <span className={`pill pill--${tone}`}>
      {icon ? <Icon name={icon} size={12} /> : null}
      {context ? <span className="visually-hidden">{context}: </span> : null}
      {text}
    </span>
  );
}
