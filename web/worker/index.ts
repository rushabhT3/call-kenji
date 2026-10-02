/**
 * Serves the page from Workers static assets and forwards the voice API to the voice server,
 * so the browser talks to one origin. The visitor's address travels in a header the voice
 * server only trusts when it carries the shared proxy secret.
 */

interface Env {
  ASSETS: Fetcher;
  VOICE_SERVER_URL: string;
  PROXY_SHARED_SECRET: string;
}

const PROXIED_PREFIXES = ["/api/", "/ws/"];

function isProxied(pathname: string): boolean {
  return PROXIED_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

function forward(request: Request, env: Env): Promise<Response> {
  const incoming = new URL(request.url);
  const target = new URL(incoming.pathname + incoming.search, env.VOICE_SERVER_URL);
  const headers = new Headers(request.headers);
  headers.set("X-Kenji-Proxy", env.PROXY_SHARED_SECRET);
  headers.set("X-Client-Address", request.headers.get("CF-Connecting-IP") ?? "unknown");
  return fetch(new Request(target, { method: request.method, headers, body: request.body }));
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const { pathname } = new URL(request.url);
    return isProxied(pathname) ? forward(request, env) : env.ASSETS.fetch(request);
  },
} satisfies ExportedHandler<Env>;
