import timeline from "./timeline.json";

export const FPS = timeline.fps;
export const WIDTH = 1920;
export const HEIGHT = 1080;
export const DURATION_FRAMES = Math.round(timeline.durationSecs * FPS);

export const COLOR = {
  paper: "#f9d66a",
  paperDeep: "#f0c64f",
  white: "#fdfcf9",
  ink: "#1e191a",
  red: "#d64b40",
  orange: "#e8954f",
  green: "#5fa06d",
  teal: "#66b1c4",
  blue: "#5ca8d4",
  night: "#0a0808",
};

export const FONT = {
  trailer: "'Bebas Neue', 'Oswald', sans-serif",
  marker: "'Permanent Marker', 'Yusei Magic', sans-serif",
  ja: "'Yusei Magic', sans-serif",
  subtitle: "'Oswald', sans-serif",
};

export const LETTERBOX = 118;

export const frames = (secs: number): number => Math.round(secs * FPS);

export { timeline };
