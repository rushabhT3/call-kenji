import { HOLD_HINT } from "../call/copy.ts";
import { Button } from "../ui/Button.tsx";

interface HoldButtonProps {
  isOnHold: boolean;
  onToggle: () => void;
}

/** Lets the caller think aloud: Kenji waits to answer until they press Done. */
export function HoldButton({ isOnHold, onToggle }: HoldButtonProps) {
  return (
    <Button icon="pause" aria-pressed={isOnHold} title={HOLD_HINT} onClick={onToggle}>
      {isOnHold ? "Done" : "Hold"}
    </Button>
  );
}
