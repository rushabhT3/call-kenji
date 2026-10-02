import type { CallView } from "../call/callView.ts";
import { COMPLIANCE_CHECKS } from "../call/copy.ts";
import { formatCount } from "../format.ts";

function complianceChip(view: CallView): string {
  const compliance = view.compliance;
  if (compliance === null) {
    return "Compliance pending";
  }
  const passing = COMPLIANCE_CHECKS.filter(({ key }) => compliance[key] === "pass").length;
  return `Compliance ${String(passing)} of ${String(COMPLIANCE_CHECKS.length)} pass`;
}

export function SummaryChips({ view }: { view: CallView }) {
  const latest = view.latency.at(-1);
  const chips = [
    { href: "#compliance", label: complianceChip(view) },
    {
      href: "#latency",
      label: latest ? `Latency ${formatCount(latest.total_ms)} ms` : "Latency —",
    },
    { href: "#strategist", label: view.strategist ? "Strategist advice" : "Strategist waiting" },
    { href: "#turn", label: view.turn ? `Turn: ${view.turn.verdict}` : "Turn —" },
  ];
  return (
    <nav className="chips" aria-label="Jump to a card">
      {chips.map((chip) => (
        <a key={chip.href} className="pill pill--pending chips__link" href={chip.href}>
          {chip.label}
        </a>
      ))}
    </nav>
  );
}
