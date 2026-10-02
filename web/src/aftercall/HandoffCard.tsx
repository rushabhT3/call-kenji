import type { HandoffRecorded } from "../contract/events.ts";
import { formatTime } from "../format.ts";
import { Card, Row } from "../ui/Card.tsx";
import { Pill } from "../ui/Pill.tsx";

function HandoffDetails({ handoff }: { handoff: HandoffRecorded }) {
  const isVerified = handoff.identity_status === "verified";
  return (
    <dl className="rows">
      <Row label="Reason" labelJa="理由">
        <span lang="ja">{handoff.reason}</span>
      </Row>
      <Row label="Summary" labelJa="要約">
        {handoff.summary}
      </Row>
      <Row label="Identity" labelJa="本人確認">
        <Pill
          tone={isVerified ? "pass" : "pending"}
          label={isVerified ? "Verified" : "Unverified"}
        />
      </Row>
      <Row label="Requested at" labelJa="時刻">
        <time className="metric-sm" dateTime={handoff.requested_at}>
          {formatTime(handoff.requested_at)} JST
        </time>
      </Row>
    </dl>
  );
}

export function HandoffCard({ handoff }: { handoff: HandoffRecorded | null }) {
  if (handoff === null) {
    return (
      <Card
        id="handoff"
        title="Handoff record"
        titleJa="引き継ぎ"
        summary="No handoff on this call."
        isEmpty
      />
    );
  }
  return (
    <Card
      id="handoff"
      title="Handoff record"
      titleJa="引き継ぎ"
      summary="You asked for a person. This is what a staff member would receive."
    >
      <HandoffDetails handoff={handoff} />
    </Card>
  );
}
