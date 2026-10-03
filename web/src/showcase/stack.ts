export interface StackItem {
  name: string;
  role: string;
  text: string;
  href: string;
  kind: "open source" | "service";
}

export const STACK: readonly StackItem[] = [
  {
    name: "Pipecat",
    role: "The voice pipeline",
    text: "Audio frames in, through speech recognition, the model and the voice, and back out, over WebRTC or a phone line.",
    href: "https://github.com/pipecat-ai/pipecat",
    kind: "open source",
  },
  {
    name: "Pipecat Flows",
    role: "The call as steps",
    text: "Greeting, identity, balance, negotiation, read-back, close: each step only gets the tools it is allowed to use. Now part of Pipecat itself.",
    href: "https://github.com/pipecat-ai/pipecat",
    kind: "open source",
  },
  {
    name: "Smart Turn v3",
    role: "Have you finished?",
    text: "An open model that hears from your voice alone whether you've finished. It runs on the CPU, one per call.",
    href: "https://github.com/pipecat-ai/smart-turn",
    kind: "open source",
  },
  {
    name: "Silero VAD",
    role: "You started talking",
    text: "Hears your first syllable in milliseconds, so Kenji knows at once when you talk over him.",
    href: "https://github.com/snakers4/silero-vad",
    kind: "open source",
  },
  {
    name: "SenseVoice + sherpa-onnx",
    role: "How you sound",
    text: "Hears the emotion and sounds such as laughter in your longer lines, and passes them to the strategist. Optional: it runs once its model is fetched.",
    href: "https://github.com/FunAudioLLM/SenseVoice",
    kind: "open source",
  },
  {
    name: "wavesurfer.js",
    role: "The demo you can scrub",
    text: "Draws the recorded call as a waveform, with Kenji's and the caller's stretches marked.",
    href: "https://github.com/katspaugh/wavesurfer.js",
    kind: "open source",
  },
  {
    name: "GSAP",
    role: "This page",
    text: "Scroll-driven animation: the pinned X-ray, the drawn diagrams, the counting numbers.",
    href: "https://github.com/greensock/GSAP",
    kind: "open source",
  },
  {
    name: "Soniox",
    role: "Japanese ears",
    text: "Streaming Japanese speech recognition that judges the end of a turn from words and intonation, not a silence timer.",
    href: "https://soniox.com/",
    kind: "service",
  },
  {
    name: "Meta Muse Spark",
    role: "The brain",
    text: "One reasoning model in three jobs: Kenji's talker, the strategist and the translator for the English subtitles.",
    href: "https://ai.meta.com/",
    kind: "service",
  },
  {
    name: "Cartesia Sonic",
    role: "Kenji's voice",
    text: "Japanese speech, fed through my kana normaliser so amounts, dates and counts are read the way a person would.",
    href: "https://cartesia.ai/",
    kind: "service",
  },
  {
    name: "Twilio",
    role: "The phone line",
    text: "Media Streams for a real phone call, and a browser softphone that crosses Twilio's network without buying a number.",
    href: "https://www.twilio.com/docs/voice/media-streams",
    kind: "service",
  },
  {
    name: "Cloudflare Workers",
    role: "The front door",
    text: "Built to serve the page and proxy the voice server on the same origin. Cloudflare's TURN relay carries audio on strict networks.",
    href: "https://workers.cloudflare.com/",
    kind: "service",
  },
];
