import { useEffect, useState } from "react";
import { loadRecording, recordingAudioUrl } from "../call/demoReplay.ts";
import { toTimeline, type Timeline } from "./timeline.ts";

export type RecordingLoad =
  | { status: "loading" }
  | { status: "failed" }
  | { status: "ready"; timeline: Timeline; audioUrl: string | null };

/** The demo's recorded call, and its sound when the replay runs at normal speed. */
export function useRecording(isEnabled: boolean, speed: number): RecordingLoad {
  const [load, setLoad] = useState<RecordingLoad>({ status: "loading" });
  useEffect(() => {
    if (!isEnabled) {
      return undefined;
    }
    let isCancelled = false;
    const run = async () => {
      try {
        const recording = await loadRecording();
        if (!isCancelled) {
          const audioUrl = recordingAudioUrl(recording, speed);
          setLoad({ status: "ready", timeline: toTimeline(recording), audioUrl });
        }
      } catch {
        if (!isCancelled) {
          setLoad({ status: "failed" });
        }
      }
    };
    void run();
    return () => {
      isCancelled = true;
    };
  }, [isEnabled, speed]);
  return load;
}
