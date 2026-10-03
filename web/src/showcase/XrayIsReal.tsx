import { EVENT_ROUTES } from "./content.ts";
import { PipelineMap } from "./PipelineMap.tsx";

function EventRoutes() {
  return (
    <ul className="event-routes">
      {EVENT_ROUTES.map((route) => (
        <li key={route.card} className="event-route comic-reveal">
          <ul className="event-route__events" aria-label={`Events feeding ${route.card}`}>
            {route.events.map((event) => (
              <li key={event} className="event-chip">
                {event}
              </li>
            ))}
          </ul>
          <span className="event-route__arrow" aria-hidden="true">
            →
          </span>
          <span className="event-route__card">{route.card}</span>
        </li>
      ))}
    </ul>
  );
}

export function XrayIsReal() {
  return (
    <section className="showcase-section" aria-labelledby="real-title">
      <div className="showcase__container showcase-split showcase-split--diagram">
        <div>
          <p className="comic-label">Is the X-ray real?</p>
          <h2 id="real-title" className="showcase-heading">
            Every card, from the call itself
          </h2>
          <p className="showcase-lead">
            While you talk, the server publishes 14 kinds of events over a WebSocket that only your
            tab can join. Every X-ray card is drawn from those events: no mock data, no canned
            animation. Only your character's facts come from a file. The demo is a recorded call:
            the same events and both voices, on the same clock.
          </p>
          <EventRoutes />
        </div>
        <div className="showcase-diagram">
          <PipelineMap />
        </div>
      </div>
    </section>
  );
}
