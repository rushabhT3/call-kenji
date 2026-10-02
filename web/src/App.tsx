import { PipecatClientAudio, PipecatClientProvider } from "@pipecat-ai/client-react";
import { useMemo } from "react";
import { isDemoMode, replaySpeed } from "./call/demoReplay.ts";
import { useBrowserCall, type BrowserCall } from "./call/useBrowserCall.ts";
import { useCallFeed, type CallFeed } from "./call/useCallFeed.ts";
import { useDemoSound } from "./call/useDemoSound.ts";
import { CallPanel } from "./landing/CallPanel.tsx";
import { Explainer } from "./landing/Explainer.tsx";
import { Hero } from "./landing/Hero.tsx";
import { RoleCard } from "./landing/RoleCard.tsx";
import { SiteHeader } from "./landing/SiteHeader.tsx";
import { useScrollToHash } from "./landing/useScrollToHash.ts";
import { LiveView } from "./xray/LiveView.tsx";

const PHONE_NUMBER: string | null =
  (import.meta.env.VITE_PHONE_NUMBER as string | undefined) ?? null;

function Landing({ feed, call }: { feed: CallFeed; call: BrowserCall }) {
  useScrollToHash();
  return (
    <>
      <SiteHeader homeHref="/">
        <a className="caption site-header__link" href="#how-to-read">
          <span className="site-header__link-long">How to read the X-ray</span>
          <span className="site-header__link-short">How it works</span>
        </a>
        <a className="caption site-header__link" href="/?demo=1">
          <span className="site-header__link-long">Watch a demo call</span>
          <span className="site-header__link-short">Demo</span>
        </a>
      </SiteHeader>
      <main className="container landing">
        <Hero />
        <div className="play">
          <RoleCard />
          <CallPanel
            phoneNumber={PHONE_NUMBER}
            code={feed.code}
            callState={call.state}
            callError={call.error}
            canCall={feed.viewerId !== null}
            onCall={() => void call.start()}
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
  const call = useBrowserCall(feed.viewerId);
  const demoSound = useDemoSound(feed.demoAudio);
  const showsLive = options.isDemo || feed.view.status !== "waiting";
  return (
    <PipecatClientProvider client={call.client}>
      <PipecatClientAudio />
      {showsLive ? (
        <LiveView
          view={feed.view}
          isDemo={options.isDemo}
          call={options.isDemo ? null : call}
          isFeedLost={!options.isDemo && feed.feedStatus === "lost"}
          startedAtMs={feed.startedAtMs}
          endedAtMs={feed.endedAtMs}
          demoSound={demoSound}
        />
      ) : (
        <Landing feed={feed} call={call} />
      )}
    </PipecatClientProvider>
  );
}
