# Status

Last updated: 2026-10-02

## Phases

- [x] **1. Setup and research** — versions, docs, design references, `docs/DESIGN.md` draft; hexagonal skeleton, Makefile, `.env.example`, CI. Check: CI green on an empty suite.
- [ ] **2. Domain logic and tests** — Check: pytest green, 100% coverage of `domain/`, required cases included.
- [ ] **3. Voice in the browser** — SmallWebRTC + prebuilt client. Check: normal path reaches a promise; spouse path discloses nothing; human request writes a handoff record; p50 latency < 1.5 s.
- [ ] **4. Conversation tests** — text-mode flows with a fake LLM + real-LLM smoke. Check: real-LLM smoke passes 3 times in a row.
- [ ] **5. Live page** — per `docs/DESIGN.md`, wired to bot events, demo mode. Check: Playwright green on demo mode; screenshots at 1440/390; design review fixes applied.
- [ ] **6. Phone line** — Twilio Media Streams, DTMF code linking. Check: real call shows only in the linked tab.
- [ ] **7. Deploy** — hosting choice + guardrails + budget alert. Check: live smoke; one phone and one browser call complete.
- [ ] **8. README and launch** — Check: fresh clone runs from README; hiring-manager review gaps fixed.

## Current phase

Phase 2 (domain logic) — code and tests written ahead of the gate; Phase 3 (voice in the browser) in progress.

## Done

- Phase 1: versions pinned (`docs/VERSIONS.md`), design references measured (`docs/DESIGN.md`), hexagonal skeleton, Makefile, `.env.example`, CI (Python lint + tests, web lint + unit + e2e). CI green on the first push.

## Next

- Gate review of Phase 2 (domain: 100% line and branch coverage).
- Phase 3: own FastAPI app with SmallWebRTC, Pipecat Flows talker, strategist, backchannel turn strategy, kana text transform, live event feed.

## Blockers

- Phase 3 real calls need `OPENAI_API_KEY`, `SONIOX_API_KEY` and `CARTESIA_API_KEY` in `.env` (paid usage; owner to provide).
- Local Windows: pnpm 10's switch to the pinned pnpm 12 fails; run `npx pnpm@12.8.1` or `make PNPM="npx -y pnpm@12.8.1"`.
