import "../showcase/showcase.css";
import "./trailer.css";
import { Burst } from "../showcase/Burst.tsx";
import { ShowcaseNav } from "../showcase/ShowcaseNav.tsx";
import { CinemaScreen } from "./CinemaScreen.tsx";
import { TRAILER_DESCRIPTION } from "./content.ts";
import { TrailerLinks } from "./TrailerLinks.tsx";
import { useTrailerVideo } from "./useTrailerVideo.ts";

const DESCRIPTION_ID = "trailer-description";

function TrailerTitle() {
  return (
    <header className="trailer__header">
      <p className="comic-label trailer__kicker">
        Now showing · <span lang="ja">上映中</span>
      </p>
      <Burst className="trailer__burst" seed={17}>
        <h1 className="burst__word">
          Call Kenji<span className="visually-hidden">: the trailer</span>
        </h1>
        <p className="burst__ja comic-ja" lang="ja">
          予告編
        </p>
      </Burst>
    </header>
  );
}

export function TrailerPage() {
  const { videoRef, state, actions } = useTrailerVideo();
  return (
    <div className="showcase trailer">
      <title>Call Kenji · The trailer</title>
      <ShowcaseNav />
      <main className="showcase__container trailer__main">
        <TrailerTitle />
        <CinemaScreen
          videoRef={videoRef}
          state={state}
          actions={actions}
          descriptionId={DESCRIPTION_ID}
        />
        {state.isPlayRefused ? (
          <p className="trailer__note" role="status">
            The browser would not start the video. Press Play again, or use the player's own
            controls.
          </p>
        ) : null}
        <p id={DESCRIPTION_ID} className="trailer__description">
          {TRAILER_DESCRIPTION}
        </p>
        <TrailerLinks />
      </main>
    </div>
  );
}
