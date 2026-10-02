import { afterEach, describe, expect, it, vi } from "vitest";
import { openViewerFeed, viewerSocketUrl, type ViewerHandlers } from "./viewerFeed.ts";

class FakeSocket extends EventTarget {
  static latest: FakeSocket | null = null;

  constructor(readonly url: string) {
    super();
    FakeSocket.latest = this;
  }

  receive(message: unknown): void {
    this.dispatchEvent(new MessageEvent("message", { data: JSON.stringify(message) }));
  }

  close(): void {
    this.dispatchEvent(new Event("close"));
  }
}

function openFakeFeed(): { handlers: ViewerHandlers; socket: FakeSocket } {
  vi.stubGlobal("WebSocket", FakeSocket);
  const handlers = { onReady: vi.fn(), onEvent: vi.fn(), onStatus: vi.fn() };
  openViewerFeed("ws://localhost/ws/viewer", handlers);
  if (FakeSocket.latest === null) {
    throw new Error("the feed did not open a socket");
  }
  return { handlers, socket: FakeSocket.latest };
}

const ready = (code: string) => ({ type: "viewer_ready", viewer_id: "viewer-1", code });

afterEach(() => {
  vi.unstubAllGlobals();
  FakeSocket.latest = null;
});

describe("openViewerFeed", () => {
  it("passes on a refreshed code so it replaces the one shown", () => {
    const { handlers, socket } = openFakeFeed();

    socket.receive(ready("4821"));
    socket.receive(ready("0937"));

    expect(handlers.onReady).toHaveBeenNthCalledWith(1, "viewer-1", "4821");
    expect(handlers.onReady).toHaveBeenLastCalledWith("viewer-1", "0937");
  });

  it("keeps delivering call events after a code refresh", () => {
    const { handlers, socket } = openFakeFeed();
    const event = { type: "flow_node", node: "greeting" };

    socket.receive(ready("4821"));
    socket.receive(ready("0937"));
    socket.receive(event);

    expect(handlers.onEvent).toHaveBeenCalledWith(event);
    expect(handlers.onStatus).not.toHaveBeenCalledWith("lost");
  });
});

describe("viewerSocketUrl", () => {
  it("uses a secure socket on a secure page", () => {
    expect(viewerSocketUrl({ protocol: "https:", host: "kenji.example" })).toBe(
      "wss://kenji.example/ws/viewer",
    );
    expect(viewerSocketUrl({ protocol: "http:", host: "localhost:5173" })).toBe(
      "ws://localhost:5173/ws/viewer",
    );
  });
});
