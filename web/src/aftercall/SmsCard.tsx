import type { SmsPreview } from "../contract/events.ts";
import { Card } from "../ui/Card.tsx";
import { Pill } from "../ui/Pill.tsx";

const graphemes = new Intl.Segmenter("ja", { granularity: "grapheme" });

function characterCount(text: string): number {
  return Array.from(graphemes.segment(text)).length;
}

export function SmsCard({ sms }: { sms: SmsPreview | null }) {
  if (sms === null) {
    return (
      <Card
        id="sms"
        title="SMS preview"
        titleJa="SMS"
        summary="No follow-up message for this outcome."
        isEmpty
      />
    );
  }
  return (
    <Card
      id="sms"
      title="SMS preview"
      titleJa="SMS"
      summary="The confirmation Kenji would send. This demo never sends it."
      status={<Pill tone="info" label="Not sent · 未送信" />}
    >
      <div className="sms">
        <p className="sms__ja" lang="ja">
          {sms.ja}
        </p>
        <p className="sms__en" lang="en">
          {sms.en}
        </p>
      </div>
      <p className="caption numeric">{characterCount(sms.ja)} characters</p>
    </Card>
  );
}
