import { UNMUTE_TO_SAY } from "../call/copy.ts";
import type { CallerClips } from "../call/useCallerClips.ts";
import type { PersonaPhrase } from "../contract/personas.ts";
import { Button } from "../ui/Button.tsx";

/** A live browser call, which can say a line for the caller. */
export interface LineSpeaker {
  clips: CallerClips;
  isMuted: boolean;
}

interface PhraseHintsProps {
  phrases: readonly PersonaPhrase[];
  /** Null where nothing can be said for the caller: a phone call or a replay. */
  speaker: LineSpeaker | null;
}

function SayItButton({ phrase, speaker }: { phrase: PersonaPhrase; speaker: LineSpeaker }) {
  const sayingUrl = speaker.clips.sayingUrl;
  const isSaying = sayingUrl === phrase.clip;
  const isUnavailable = speaker.isMuted || sayingUrl !== null;
  return (
    <Button
      size="sm"
      icon="sound"
      isBusy={isSaying}
      aria-disabled={isUnavailable}
      onClick={
        isUnavailable
          ? undefined
          : () => {
              speaker.clips.say(phrase.clip);
            }
      }
    >
      {isSaying ? "Saying…" : "Say it"}
      <span className="visually-hidden">: {phrase.label}</span>
    </Button>
  );
}

function Hint({ phrase, speaker }: { phrase: PersonaPhrase; speaker: LineSpeaker | null }) {
  return (
    <li className="hint">
      <div className="hint__text">
        <p className="hint__label">{phrase.label}</p>
        <p className="hint__ja" lang="ja">
          {phrase.ja}
        </p>
        <p className="hint__en">{phrase.en}</p>
      </div>
      {speaker ? <SayItButton phrase={phrase} speaker={speaker} /> : null}
    </li>
  );
}

/** What the caller could say at the step Kenji is at, in their persona's words. */
export function PhraseHints({ phrases, speaker }: PhraseHintsProps) {
  return (
    <div className="hints">
      <h3 id="hints-title" className="caption">
        Your turn · <span lang="ja">あなたの番</span>
      </h3>
      {phrases.length === 0 ? (
        <p className="hints__empty">Listen to Kenji.</p>
      ) : (
        <ul className="hints__list" aria-labelledby="hints-title">
          {phrases.map((phrase) => (
            <Hint key={phrase.id} phrase={phrase} speaker={speaker} />
          ))}
        </ul>
      )}
      {speaker?.isMuted ? <p className="hints__note">{UNMUTE_TO_SAY}</p> : null}
      {speaker?.clips.error ? (
        <p className="hints__error" role="alert">
          {speaker.clips.error}
        </p>
      ) : null}
    </div>
  );
}
