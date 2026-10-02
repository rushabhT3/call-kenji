# Status

Last updated: 2026-10-02

## Phases

- [x] **1. Setup and research** — versions, docs, design references, `docs/DESIGN.md` draft; hexagonal skeleton, Makefile, `.env.example`, CI. Check: CI green on an empty suite.
- [x] **2. Domain logic and tests** — Check: pytest green, 100% coverage of `domain/`, required cases included.
- [x] **3. Voice in the browser** — SmallWebRTC + prebuilt client. Check: normal path reaches a promise; spouse path discloses nothing; human request writes a handoff record; p50 latency < 1.5 s.
- [x] **4. Conversation tests** — text-mode flows with a fake LLM + real-LLM smoke. Check: real-LLM smoke passes 3 times in a row.
- [x] **5. Live page** — per `docs/DESIGN.md`, wired to bot events, demo mode. Check: Playwright green on demo mode; screenshots at 1440/390; design review fixes applied.
- [ ] **6. Phone line** — Twilio Media Streams, DTMF code linking. Check: real call shows only in the linked tab.
- [ ] **7. Deploy** — hosting choice + guardrails + budget alert. Check: live smoke; one phone and one browser call complete.
- [ ] **8. README and launch** — Check: fresh clone runs from README; hiring-manager review gaps fixed.

## Current phase

Phase 3 passes on real voice. With Soniox, Muse Spark and Cartesia over a real WebRTC connection
(`scripts/voice_check.py`, a second Cartesia voice as the caller), all three paths pass:

- normal: a promise is recorded, the AI disclosure is given and the audit chain verifies;
- spouse: Kenji says nothing about the debt and asks for a call back;
- human request: the handoff record is written.

Turn latency on those calls: p50 760 ms, p95 931 ms (promise call); p50 704 ms, p95 890 ms
(handoff and spouse calls). Measured from the caller's own audio, Kenji is heard about 0.93 s
after the caller stops. Three changes got there (DECISIONS #29 to #31):

- predictable turns are answered from rules, through the same tools, without the model;
- every other turn opens with an instant 「はい、」, and Kenji keeps the floor until his answer;
- a talker request that has not started streaming after 2.5 s is raced by a second one.

Muse Spark's own answers still take 2 to 6 s on the turns it handles: its thinking cannot be
switched off (`reasoning_effort` `none` returns HTTP 400 in both APIs), and Muse Glimmer is not on
the Meta Model API.

Correctness held. A nine-scenario test against the real model passed 27 of 27 runs, and the
real-model suite passes. The nine scenarios: normal, 平成 birth date, spouse, ¥3,000 bargainer,
handoff, stop contact, asking the amount before identity, three wrong birth dates, and a
read-back correction.

The real calls exposed bugs the text harness could not, all fixed:

- Step changes after Kenji's scripted lines fired a turn late or never (DECISIONS #25).
- A silence timer split 「生年月日は、」 from the date that followed (DECISIONS #24). The identity
  answer with that pause has since passed on the first try in 4 of 4 calls.
- The read-back could be heard as six payments plus a seventh (DECISIONS #27).
- The strategist proposed plans outside the terms (DECISIONS #28).
- The live page showed a replayed call's length at the replay speed.

## Done

- Phase 1: versions pinned (`docs/VERSIONS.md`), design references measured (`docs/DESIGN.md`), hexagonal skeleton, Makefile, `.env.example`, CI. CI green on the first push.
- Phase 2: 100% line and branch coverage of `domain/`, all required cases, gate review findings fixed.
- Phase 3 (code): FastAPI server, Flows talker, strategist, backchannel strategy, kana TTS transform, guardrails, live event feed, per-call ICE servers. The text-mode harness runs the real call assembly.
- Phase 4: normal, spouse, ¥3,000 bargainer, human handoff and stop-contact scenarios pass in text mode with a scripted talker. With Muse Spark as the talker and strategist, `pytest -m real_llm` passed 5/5 three times in a row on commit 92029fb (78 s, 76 s, 89 s).
- Phase 5: live page per `docs/DESIGN.md`, demo replay with no backend, 32 Playwright tests (WCAG AA scans, overflow at 1440, 1024, 768 and 390), screenshots in `docs/screenshots/`, design review applied (`docs/DESIGN-REVIEW.md`). The demo replay is now a real voice call (`web/public/demo/call.json`, 140 s), recorded with `scripts/record_demo.py`.
- Phase 6 (code): signed Twilio webhook, single-use stream tokens, keypad linking to one tab, all tested with simulated Twilio messages.
- Phase 7 (prepared): Dockerfile (built in CI), Cloudflare Worker, manual Deploy workflow, `docs/DEPLOY.md`, `scripts/smoke.py`.
- Phase 8 (draft): README with pitch, diagram, real vs simulated, cost, run steps, recording script and launch post.
- Interim gate review (Phases 3 to 8), all findings fixed:
  - call records are written off the event loop and uploaded once per call;
  - refused phone calls are turned away at the webhook, so no media stream opens;
  - finished calls leave the in-memory hub;
  - the AI disclosure cannot be interrupted;
  - the greeting says the model provider may use the conversation;
  - corrections over the read-back interrupt;
  - the strategist schema comes from the `Advice` model;
  - the link code refreshes every 5 minutes;
  - the deploy settings and lifecycle rule are fixed;
  - WCAG AA scans, plus overflow checks at 1440, 1024, 768 and 390;
  - tests for the time limit, a hanging strategist and the real adapters' wiring.
- Muse Spark probed on 2026-10-02: the `developer` role and strict JSON output work (`docs/VERSIONS.md`).

## Next

1. One real browser call by a person during calling hours (08:00 to 21:00 Japan time).
2. Buy the Twilio number (owner approval: a US local number, $1.15 a month) and make the real phone-call check.
3. Deploy (owner approval), run the smoke test, one phone call and one browser call.
4. Fresh-clone check of the README and the hiring-manager review.

## Blockers

- Number purchase and public deploy need the owner's go-ahead.
- Local Windows: pnpm 10 cannot switch itself to the pinned pnpm 12, so use `npx pnpm@12.8.1` or `make PNPM="npx -y pnpm@12.8.1"`.
