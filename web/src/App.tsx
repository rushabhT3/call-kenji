import { PipecatClientAudio, PipecatClientProvider } from "@pipecat-ai/client-react";
import { useMemo } from "react";
import { isDemoMode, replaySpeed } from "./call/demoReplay.ts";
import { useBrowserCall, type BrowserCall } from "./call/useBrowserCall.ts";
import { useCallFeed, type CallFeed } from "./call/useCallFeed.ts";
import { ReplayContext } from "./demo/replayContext.ts";
import { CallPanel } from "./landing/CallPanel.tsx";
import { Explainer } from "./landing/Explainer.tsx";
import { Hero } from "./landing/Hero.tsx";
import { RoleCard } from "./landing/RoleCard.tsx";
import { LandingHeader } from "./landing/LandingHeader.tsx";
import { useScrollToHash } from "./landing/useScrollToHash.ts";
import { useSoftphone } from "./call/useSoftphone.ts";
import { personaIdForCall, personaShownOnCall } from "./persona/catalog.ts";
import { usePersonaCatalog, type PersonaCatalogLoad } from "./persona/usePersonaCatalog.ts";
import { usePersonaChoice, type PersonaChoice } from "./persona/usePersonaChoice.ts";
import { LiveView } from "./xray/LiveView.tsx";

const PHONE_NUMBER: string | null =
  (import.meta.env.VITE_PHONE_NUMBER as string | undefined) ?? null;

interface LandingProps {
  feed: CallFeed;
  call: BrowserCall;
  personas: PersonaCatalogLoad;
  choice: PersonaChoice;
}

/** The softphone, set to ring as the persona chosen here. */
function softphoneFor(url: string | null, personaId: string): string | null {
  return url ? `${url}?persona=${encodeURIComponent(personaId)}` : null;
}

function Landing({ feed, call, personas, choice }: LandingProps) {
  useScrollToHash(personas.catalog.status !== "loading");
  const softphone = useSoftphone();
  return (
    <>
      <LandingHeader />
      <main className="container landing">
        <Hero />
        <div className="play">
          <RoleCard
            catalog={personas.catalog}
            chosen={choice.chosen}
            onChoose={choice.choose}
            onSurprise={choice.surprise}
            onRetry={personas.retry}
          />
          <CallPanel
            phoneNumber={PHONE_NUMBER}
            code={feed.code}
            callState={call.state}
            callError={call.error}
            canCall={feed.viewerId !== null}
            onCall={() => void call.start()}
            softphoneUrl={softphoneFor(
              softphone,
              personaIdForCall(personas.catalog, choice.chosenId),
            )}
          />
        </div>
        <Explainer />
      </main>
    </>
  );
}

export function App() {
  const options = useMemo(
    () => ({
      isDemo: isDemoMode(window.location.search),
      speed: replaySpeed(window.location.search),
    }),
    [],
  );
  const feed = useCallFeed(options);
  const personas = usePersonaCatalog();
  const choice = usePersonaChoice(personas.catalog);
  const call = useBrowserCall(feed.viewerId, personaIdForCall(personas.catalog, choice.chosenId));
  const showsLive = options.isDemo || feed.view.status !== "waiting";
  const persona = personaShownOnCall(personas.catalog, {
    startedId: feed.view.personaId,
    chosenId: options.isDemo ? null : choice.chosenId,
  });
  return (
    <PipecatClientProvider client={call.client}>
      <PipecatClientAudio />
      {showsLive ? (
        <ReplayContext value={feed.replay}>
          <LiveView
            view={feed.view}
            isDemo={options.isDemo}
            call={options.isDemo ? null : call}
            isFeedLost={!options.isDemo && feed.feedStatus === "lost"}
            startedAtMs={feed.startedAtMs}
            endedAtMs={feed.endedAtMs}
            persona={persona}
          />
        </ReplayContext>
      ) : (
        <Landing feed={feed} call={call} personas={personas} choice={choice} />
      )}
    </PipecatClientProvider>
  );
}
