import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { SplitText } from "gsap/SplitText";

const EASE_SMOOTH = "power3.out";
const EASE_POP = "back.out(1.7)";
const EASE_BOUNCE = "elastic.out(1, 0.55)";
const REVEAL_START = "top 85%";
const PINNED_CLASS = "is-pinned";
const PANELS = ".comic-reveal, .stack-card";
const SCREEN = ".xray-reveal__screen";
/** How far the reader scrolls, as a share of the screen height, for each scene of the X-ray. */
const SCROLL_PER_SCENE = 90;

type Cleanup = () => void;

function stepsInOrder(diagram: Element): Element[] {
  return Array.from(diagram.querySelectorAll<SVGElement>(".diagram-step")).sort(
    (first, second) => Number(first.dataset.step) - Number(second.dataset.step),
  );
}

/** Adds a tween only when there is something to move; GSAP warns about empty targets. */
function fromAny(
  timeline: gsap.core.Timeline,
  targets: ArrayLike<Element>,
  vars: gsap.TweenVars,
  position?: gsap.Position,
): void {
  if (targets.length > 0) {
    timeline.from(targets, vars, position);
  }
}

function revealHero(root: HTMLElement): void {
  const timeline = gsap.timeline({ defaults: { ease: EASE_SMOOTH } });
  timeline
    .from(".showcase-hero__burst", {
      scale: 0.3,
      rotate: -14,
      autoAlpha: 0,
      duration: 1,
      ease: EASE_BOUNCE,
    })
    .from(root.querySelectorAll(".doodle"), { drawSVG: 0, duration: 1.4, stagger: 0.12 }, 0.1)
    .from(
      root.querySelectorAll(".showcase-hero__inner > :not(h1, .burst)"),
      { y: 24, autoAlpha: 0, duration: 0.7, stagger: 0.1 },
      0.8,
    );
  SplitText.create(".showcase-hero__title", {
    type: "lines,words",
    mask: "lines",
    autoSplit: true,
    // SplitText wants the tween back to re-time it after a re-split; a GSAP tween is thenable,
    // which this rule mistakes for a promise.
    // eslint-disable-next-line @typescript-eslint/no-misused-promises
    onSplit: (split) =>
      gsap.from(split.lines, { yPercent: 110, duration: 0.9, stagger: 0.08, delay: 0.35 }),
  });
}

function countUp(element: HTMLElement): Cleanup {
  const { value = "0", decimals = "0", prefix = "", suffix = "" } = element.dataset;
  const finalText = element.textContent;
  const counter = { value: 0 };
  const show = () => {
    element.textContent = `${prefix}${counter.value.toFixed(Number(decimals))}${suffix}`;
  };
  show();
  gsap.to(counter, {
    value: Number(value),
    duration: 1.6,
    ease: "power2.out",
    onUpdate: show,
    scrollTrigger: { trigger: element, start: REVEAL_START },
  });
  return () => {
    element.textContent = finalText;
  };
}

function popStats(root: HTMLElement): Cleanup {
  gsap.from(".stat__burst", {
    scale: 0,
    rotate: -20,
    autoAlpha: 0,
    duration: 0.8,
    ease: EASE_POP,
    stagger: 0.12,
    scrollTrigger: { trigger: ".stat-strip", start: REVEAL_START },
  });
  const restores = gsap.utils
    .toArray<HTMLElement>(root.querySelectorAll(".stat__value"))
    .map(countUp);
  return () => {
    restores.forEach((restore) => {
      restore();
    });
  };
}

function addCallout(timeline: gsap.core.Timeline, callout: Element, isLast: boolean): void {
  timeline.fromTo(
    callout,
    { autoAlpha: 0, x: 90, rotate: 4 },
    { autoAlpha: 1, x: 0, rotate: 0, duration: 0.5 },
  );
  if (!isLast) {
    timeline.to(callout, { autoAlpha: 0, x: -60, rotate: -3, duration: 0.4 }, "+=0.6");
  }
}

/** Apple-style: the screenshot tilts up into place, steps aside, and each card is shown in turn. */
function pinXrayReveal(root: HTMLElement): Cleanup {
  const stage = root.querySelector<HTMLElement>(".xray-reveal__stage");
  const nav = root.querySelector<HTMLElement>(".showcase-nav");
  if (!stage || !nav) {
    throw new Error("The features page is missing its X-ray stage or its top bar");
  }
  stage.classList.add(PINNED_CLASS);
  const callouts = Array.from(stage.querySelectorAll(".xray-callout"));
  const timeline = gsap.timeline({
    defaults: { ease: "none" },
    scrollTrigger: {
      trigger: stage,
      start: () => `top ${String(nav.offsetHeight)}px`,
      end: () => `+=${String((callouts.length + 1) * SCROLL_PER_SCENE)}%`,
      pin: true,
      scrub: 0.6,
      anticipatePin: 1,
      invalidateOnRefresh: true,
    },
  });
  timeline
    .from(SCREEN, {
      rotateX: 26,
      scale: 1.12,
      yPercent: 8,
      transformPerspective: 1800,
      duration: 1,
    })
    .to(SCREEN, { xPercent: -18, scale: 0.86, duration: 0.6 });
  callouts.forEach((callout, index) => {
    addCallout(timeline, callout, index === callouts.length - 1);
  });
  return () => {
    stage.classList.remove(PINNED_CLASS);
  };
}

function revealDiagram(diagram: Element): void {
  const timeline = gsap.timeline({
    defaults: { ease: EASE_POP },
    scrollTrigger: { trigger: diagram, start: "top 80%", end: "bottom 60%", scrub: 0.5 },
  });
  fromAny(timeline, stepsInOrder(diagram), {
    autoAlpha: 0,
    scale: 0.7,
    transformOrigin: "50% 50%",
    stagger: 0.15,
  });
  fromAny(timeline, diagram.querySelectorAll(".diagram-draw"), { drawSVG: 0, stagger: 0.12 }, 0);
  fromAny(timeline, diagram.querySelectorAll(".latency-bar"), { scaleX: 0, stagger: 0.1 }, 0.2);
  fromAny(timeline, diagram.querySelectorAll(".latency-callout"), { autoAlpha: 0, y: 12 });
}

function revealPanels(root: HTMLElement, selector: string): void {
  const panels = gsap.utils.toArray<Element>(root.querySelectorAll(selector));
  // Scale and lift only: the panels keep the tilt their stylesheet gives them.
  gsap.set(panels, { autoAlpha: 0, y: 40, scale: 0.94 });
  ScrollTrigger.batch(panels, {
    start: REVEAL_START,
    once: true,
    onEnter: (batch) =>
      gsap.to(batch, { autoAlpha: 1, y: 0, scale: 1, duration: 0.7, stagger: 0.1, ease: EASE_POP }),
  });
}

/** Every scroll animation on the page; the cleanup undoes what GSAP's own revert cannot. */
export function animateShowcase(root: HTMLElement, { isPinned }: { isPinned: boolean }): Cleanup {
  revealHero(root);
  const restoreStats = popStats(root);
  const unpin = isPinned ? pinXrayReveal(root) : () => undefined;
  root.querySelectorAll(".diagram").forEach(revealDiagram);
  revealPanels(root, isPinned ? PANELS : `${PANELS}, .xray-callout`);
  return () => {
    restoreStats();
    unpin();
  };
}
