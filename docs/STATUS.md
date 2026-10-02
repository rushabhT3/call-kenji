# Status

Last updated: 2026-10-02

## Phases

- [x] **1. Setup and research** — versions, docs, design references, `docs/DESIGN.md` draft; hexagonal skeleton, Makefile, `.env.example`, CI. Check: CI green on an empty suite.
- [x] **2. Domain logic and tests** — Check: pytest green, 100% coverage of `domain/`, required cases included.
- [ ] **3. Voice in the browser** — SmallWebRTC + prebuilt client. Check: normal path reaches a promise; spouse path discloses nothing; human request writes a handoff record; p50 latency < 1.5 s.
- [ ] **4. Conversation tests** — text-mode flows with a fake LLM + real-LLM smoke. Check: real-LLM smoke passes 3 times in a row.
- [ ] **5. Live page** — per `docs/DESIGN.md`, wired to bot events, demo mode. Check: Playwright green on demo mode; screenshots at 1440/390; design review fixes applied.
- [ ] **6. Phone line** — Twilio Media Streams, DTMF code linking. Check: real call shows only in the linked tab.
- [ ] **7. Deploy** — hosting choice + guardrails + budget alert. Check: live smoke; one phone and one browser call complete.
- [ ] **8. README and launch** — Check: fresh clone runs from README; hiring-manager review gaps fixed.

## Current phase

Every phase's code is built and tested without paid services. Real-call checks wait for API keys
(Phases 3 and 4), a phone number (Phase 6) and approval to deploy (Phase 7).

## Done

- Phase 1: versions pinned (`docs/VERSIONS.md`), design references measured (`docs/DESIGN.md`), hexagonal skeleton, Makefile, `.env.example`, CI. CI green on the first push.
- Phase 2: 100% line and branch coverage of `domain/`, all required cases, gate review findings fixed.
- Phase 3 (code): FastAPI server, Flows talker, strategist, backchannel strategy, kana TTS transform, guardrails, live event feed, per-call ICE servers. The text-mode harness runs the real call assembly.
- Phase 4 (fake-LLM part): normal, spouse, ¥3,000 bargainer, human handoff and stop-contact scenarios pass in text mode. The real-model smoke suite (`pytest -m real_llm`) is ready and skips without a key.
- Phase 5 (provisional): live page per `docs/DESIGN.md`, demo replay with no backend, 22 Playwright tests at 1440 and 390, screenshots in `docs/screenshots/`, design review applied (`docs/DESIGN-REVIEW.md`). The demo recording is a scripted text-mode run until a real call replaces it.
- Phase 6 (code): signed Twilio webhook, single-use stream tokens, keypad linking to one tab, all tested with simulated Twilio messages.
- Phase 7 (prepared): Dockerfile (built in CI), Cloudflare Worker, manual Deploy workflow, `docs/DEPLOY.md`, `scripts/smoke.py`.
- Phase 8 (draft): README with pitch, diagram, real vs simulated, cost, run steps, recording script and launch post.

## Next

1. Real browser calls once `LLM_API_KEY`, `SONIOX_API_KEY` and `CARTESIA_API_KEY` are in `.env`: normal, spouse and human paths, plus p50 latency. Then record the demo replay from a real call.
2. `pytest -m real_llm` three times in a row.
3. Buy the Twilio number (owner approval: a US local number, $1.15 a month) and make the real phone-call check.
4. Deploy (owner approval), run the smoke test, one phone call and one browser call.
5. Fresh-clone check of the README and the hiring-manager review.

## Blockers

- API keys are not in `.env` yet. Spend is approved up to $5 for test calls.
- Number purchase and public deploy need the owner's go-ahead.
- Local Windows: pnpm 10 cannot switch itself to the pinned pnpm 12, so use `npx pnpm@12.8.1` or `make PNPM="npx -y pnpm@12.8.1"`.
