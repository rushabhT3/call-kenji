import { parseCallEvent, parseViewerReady, type CallEvent } from "../contract/events.ts";

export type FeedStatus = "connecting" | "open" | "lost";

export interface ViewerHandlers {
  onReady: (viewerId: string, code: string) => void;
  onEvent: (event: CallEvent) => void;
  onStatus: (status: FeedStatus) => void;
}

export function viewerSocketUrl(location: Pick<Location, "protocol" | "host">): string {
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  return `${scheme}://${location.host}/ws/viewer`;
}

function handleMessage(data: unknown, handlers: ViewerHandlers): void {
  if (typeof data !== "string") {
    return;
  }
  const message: unknown = JSON.parse(data);
  const ready = parseViewerReady(message);
  if (ready) {
    handlers.onReady(ready.viewer_id, ready.code);
    return;
  }
  const event = parseCallEvent(message);
  if (event) {
    handlers.onEvent(event);
  }
}

export function openViewerFeed(url: string, handlers: ViewerHandlers): () => void {
  const socket = new WebSocket(url);
  handlers.onStatus("connecting");
  socket.addEventListener("open", () => {
    handlers.onStatus("open");
  });
  socket.addEventListener("message", (message) => {
    handleMessage(message.data, handlers);
  });
  socket.addEventListener("close", () => {
    handlers.onStatus("lost");
  });
  return () => {
    socket.close();
  };
}
