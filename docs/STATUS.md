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

Phase 3 code complete and tested in text mode; its real-call check waits for API keys in `.env`. Phase 5 (live page) in progress meanwhile.

## Done

- Phase 2: 100% line and branch coverage of `domain/`, all required cases, gate review findings fixed (CI green on 365d72d).
- Phase 3 (code): FastAPI server, Flows talker, strategist, backchannel strategy, kana TTS transform, guardrails, live event feed; text-mode harness runs the real call assembly (CI green on e1c2525).
- Phase 4 (fake-LLM part): normal, spouse, ¥3,000 bargainer, human handoff and stop-contact scenarios pass in text mode.
- Phase 1: versions pinned (`docs/VERSIONS.md`), design references measured (`docs/DESIGN.md`), hexagonal skeleton, Makefile, `.env.example`, CI (Python lint + tests, web lint + unit + e2e). CI green on the first push.

## Next

- Phase 3 real-call check (normal / spouse / human paths, p50 latency) once keys are in `.env`.
- Phase 4 real-LLM smoke run, 3 in a row (Muse Spark contributor).
- Phase 5 live page per `docs/DESIGN.md` with `?demo=1` replay.

## Blockers

- Real calls need `LLM_API_KEY` (Meta Muse Spark), `SONIOX_API_KEY` and `CARTESIA_API_KEY` in `.env`; owner approved test spend up to $5.
- Local Windows: pnpm 10's switch to the pinned pnpm 12 fails; run `npx pnpm@12.8.1` or `make PNPM="npx -y pnpm@12.8.1"`.
