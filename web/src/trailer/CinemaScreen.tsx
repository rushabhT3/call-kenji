import type { RefObject } from "react";
import { TRAILER_POSTER, TRAILER_VIDEO } from "./content.ts";
import { PlayButton } from "./PlayButton.tsx";
import { TrailerError } from "./TrailerError.tsx";
import type { TrailerActions, TrailerState } from "./useTrailerVideo.ts";

interface CinemaScreenProps {
  videoRef: RefObject<HTMLVideoElement | null>;
  state: TrailerState;
  actions: TrailerActions;
  descriptionId: string;
}

/** The letterboxed screen: the trailer with its play button, or a friendly card if it won't load. */
export function CinemaScreen({ videoRef, state, actions, descriptionId }: CinemaScreenProps) {
  if (state.status === "failed") {
    return <TrailerError onRetry={actions.retry} />;
  }
  return (
    <div className="trailer-screen">
      <video
        key={state.attempt}
        ref={videoRef}
        className="trailer-screen__video"
        controls
        playsInline
        preload="metadata"
        poster={TRAILER_POSTER}
        src={TRAILER_VIDEO}
        aria-label="Call Kenji trailer"
        aria-describedby={descriptionId}
        onPlay={actions.markPlaying}
        onError={actions.markFailed}
      />
      {state.status === "ready" ? (
        <PlayButton
          onPlay={() => {
            void actions.play();
          }}
        />
      ) : null}
    </div>
  );
}
