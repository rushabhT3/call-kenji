# Status

Last updated: 2026-10-02

## Phases

- [x] **1. Setup and research** — versions, docs, design references, `docs/DESIGN.md` draft; hexagonal skeleton, Makefile, `.env.example`, CI. Check: CI green on an empty suite.
- [x] **2. Domain logic and tests** — Check: pytest green, 100% coverage of `domain/`, required cases included.
- [ ] **3. Voice in the browser** — SmallWebRTC + prebuilt client. Check: normal path reaches a promise; spouse path discloses nothing; human request writes a handoff record; p50 latency < 1.5 s.
- [x] **4. Conversation tests** — text-mode flows with a fake LLM + real-LLM smoke. Check: real-LLM smoke passes 3 times in a row.
- [ ] **5. Live page** — per `docs/DESIGN.md`, wired to bot events, demo mode. Check: Playwright green on demo mode; screenshots at 1440/390; design review fixes applied.
- [ ] **6. Phone line** — Twilio Media Streams, DTMF code linking. Check: real call shows only in the linked tab.
- [ ] **7. Deploy** — hosting choice + guardrails + budget alert. Check: live smoke; one phone and one browser call complete.
- [ ] **8. README and launch** — Check: fresh clone runs from README; hiring-manager review gaps fixed.

## Current phase

Keys are in `.env` and the real-call checks have started. The real-model conversation suite passes
on Muse Spark. The first synthetic voice call (`scripts/voice_check.py`) connected over WebRTC and
Kenji's opening played through Cartesia, but Soniox refused every connection with
`402 Organization balance exhausted`, so no caller speech was recognised. Phase 3 waits for Soniox
credit.

Latency: on Muse Spark's contributor tier the talker's first token alone takes about 2.9 s
(median of 8 calls at `minimal`, network round trip 0.24 s), and 7.7 s at `xhigh`. The 1.5 s p50
gate cannot be met on this provider; a faster talker model is the owner's call.

## Done

- Phase 1: versions pinned (`docs/VERSIONS.md`), design references measured (`docs/DESIGN.md`), hexagonal skeleton, Makefile, `.env.example`, CI. CI green on the first push.
- Phase 2: 100% line and branch coverage of `domain/`, all required cases, gate review findings fixed.
- Phase 3 (code): FastAPI server, Flows talker, strategist, backchannel strategy, kana TTS transform, guardrails, live event feed, per-call ICE servers. The text-mode harness runs the real call assembly.
- Phase 4: normal, spouse, ¥3,000 bargainer, human handoff and stop-contact scenarios pass in text mode with a scripted talker. With Muse Spark as the talker and strategist, `pytest -m real_llm` passed 5/5 three times in a row on commit 92029fb (78 s, 76 s, 89 s).
- Phase 5 (provisional): live page per `docs/DESIGN.md`, demo replay with no backend, 22 Playwright tests at 1440 and 390, screenshots in `docs/screenshots/`, design review applied (`docs/DESIGN-REVIEW.md`). The demo recording is a scripted text-mode run until a real call replaces it.
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

1. Top up Soniox, then run `uv run python scripts/voice_check.py`: normal, spouse and human paths over real WebRTC, with p50 latency. Then re-record the demo replay from one of those calls.
2. One real browser call by a person during calling hours (08:00 to 21:00 Japan time).
3. Buy the Twilio number (owner approval: a US local number, $1.15 a month) and make the real phone-call check.
4. Deploy (owner approval), run the smoke test, one phone call and one browser call.
5. Fresh-clone check of the README and the hiring-manager review.

## Blockers

- Soniox: `402 Organization balance exhausted`. Speech recognition needs credit on the Soniox account.
- The 1.5 s p50 budget cannot be met with Muse Spark as the talker (about 2.9 s to the first token alone).
- Number purchase and public deploy need the owner's go-ahead.
- Local Windows: pnpm 10 cannot switch itself to the pinned pnpm 12, so use `npx pnpm@12.8.1` or `make PNPM="npx -y pnpm@12.8.1"`.
