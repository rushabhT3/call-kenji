import Daily from "@daily-co/daily-js";

/** How loud the caller hears a line said for them, so they know it went out without an echo. */
const LOCAL_MONITOR_GAIN = 0.25;

/** The caller's microphone with any recorded line mixed in, as one outgoing track. */
export interface ClipMixer {
  track: MediaStreamTrack;
  load: (clipUrl: string) => Promise<AudioBuffer>;
  /** Plays a line into the call and quietly on this device; resolves when it has been said. */
  play: (clip: AudioBuffer) => Promise<void>;
  close: () => Promise<void>;
}

interface MixGraph {
  context: AudioContext;
  /** Where the microphone and the lines meet: the track the call sends. */
  outgoing: MediaStreamAudioDestinationNode;
  /** The lines alone, quietly, to this device's speaker. */
  monitor: GainNode;
  microphone: MediaStreamTrack;
  track: MediaStreamTrack;
}

function buildMixGraph(microphone: MediaStreamTrack): MixGraph {
  const context = new AudioContext();
  const outgoing = context.createMediaStreamDestination();
  // Daily stops the microphone track it opened once another source replaces it, so the mix
  // keeps a clone of its own.
  const ownMicrophone = microphone.clone();
  context.createMediaStreamSource(new MediaStream([ownMicrophone])).connect(outgoing);
  const monitor = context.createGain();
  monitor.gain.value = LOCAL_MONITOR_GAIN;
  monitor.connect(context.destination);
  const track = outgoing.stream.getAudioTracks()[0];
  if (track === undefined) {
    throw new Error("the audio mixer produced no track");
  }
  return { context, outgoing, monitor, microphone: ownMicrophone, track };
}

async function decodeClip(context: AudioContext, clipUrl: string): Promise<AudioBuffer> {
  const response = await fetch(clipUrl);
  if (!response.ok) {
    throw new Error(`clip ${clipUrl} unavailable (${String(response.status)})`);
  }
  return context.decodeAudioData(await response.arrayBuffer());
}

function cachedLoader(context: AudioContext): (clipUrl: string) => Promise<AudioBuffer> {
  const clips = new Map<string, Promise<AudioBuffer>>();
  return async (clipUrl) => {
    const clip = clips.get(clipUrl) ?? decodeClip(context, clipUrl);
    clips.set(clipUrl, clip);
    try {
      return await clip;
    } catch (cause) {
      clips.delete(clipUrl);
      throw cause;
    }
  };
}

/** Says one line at a time: a new line cuts off the one before, as a caller would. */
function linePlayer(graph: MixGraph) {
  let current: { source: AudioBufferSourceNode; finish: () => void } | null = null;

  const stop = () => {
    current?.source.stop();
    current?.finish();
    current = null;
  };

  const play = async (clip: AudioBuffer) => {
    stop();
    await graph.context.resume();
    const source = graph.context.createBufferSource();
    source.buffer = clip;
    source.connect(graph.outgoing);
    source.connect(graph.monitor);
    await new Promise<void>((resolve) => {
      current = { source, finish: resolve };
      source.addEventListener("ended", () => {
        current = current?.source === source ? null : current;
        resolve();
      });
      source.start();
    });
  };

  return { play, stop };
}

export function createClipMixer(microphone: MediaStreamTrack): ClipMixer {
  const graph = buildMixGraph(microphone);
  const player = linePlayer(graph);
  return {
    track: graph.track,
    load: cachedLoader(graph.context),
    play: player.play,
    close: async () => {
      player.stop();
      graph.microphone.stop();
      graph.track.stop();
      await graph.context.close();
    },
  };
}

/**
 * SmallWebRTCTransport keeps the caller's media in a Daily call object and swaps a new local
 * audio track from it into the outgoing stream, so choosing a custom audio source there is the
 * supported way to change what the call sends.
 */
export async function sendAsMicrophone(track: MediaStreamTrack): Promise<void> {
  const call = Daily.getCallInstance();
  if (call === undefined) {
    throw new Error("the browser call has no Daily call object to send audio through");
  }
  await call.setInputDevicesAsync({ audioSource: track });
}
