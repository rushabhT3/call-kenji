import { useCallback, useEffect, useRef, useState } from "react";
import type { DemoAudio } from "./useCallFeed.ts";

export interface DemoSound {
  isOn: boolean;
  toggle: () => void;
}

const MILLISECONDS_PER_SECOND = 1000;

/**
 * The replay's sound, off until the visitor asks for it: browsers only play sound after a
 * press. Turned on, it joins the replay where the replay has got to.
 */
export function useDemoSound(audio: DemoAudio | null): DemoSound | null {
  const player = useRef<HTMLAudioElement | null>(null);
  const [isOn, setIsOn] = useState(false);

  useEffect(() => {
    if (audio === null) {
      return undefined;
    }
    const element = new Audio(audio.url);
    element.preload = "auto";
    const stop = () => {
      setIsOn(false);
    };
    element.addEventListener("ended", stop);
    player.current = element;
    return () => {
      element.removeEventListener("ended", stop);
      element.pause();
      player.current = null;
    };
  }, [audio]);

  const toggle = useCallback(async () => {
    const element = player.current;
    if (element === null || audio === null) {
      return;
    }
    if (isOn) {
      element.pause();
      setIsOn(false);
      return;
    }
    element.currentTime = (Date.now() - audio.startedAtMs) / MILLISECONDS_PER_SECOND;
    try {
      await element.play();
      setIsOn(true);
    } catch {
      setIsOn(false);
    }
  }, [audio, isOn]);

  return audio ? { isOn, toggle: () => void toggle() } : null;
}
