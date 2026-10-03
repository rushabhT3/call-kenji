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
- a talker request that has not started streaming after 2.5 s is raced by a second one;
- if the model says nothing for 8 s, Kenji holds, retries once, then apologises (DECISIONS #33).

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
- Phase 4: normal, spouse, ¥3,000 bargainer, human handoff and stop-contact scenarios pass in text mode with a scripted talker. With Muse Spark as the talker and strategist, `pytest -m real_llm` passed 5/5 three times in a row on commit 92029fb (78 s, 76 s, 89 s), and again after the fast path on a6b3c90 (53 s, 71 s, 58 s).
- Phase 5: live page per `docs/DESIGN.md`, demo replay with no backend, 32 Playwright tests (WCAG AA scans, overflow at 1440, 1024, 768 and 390), screenshots in `docs/screenshots/`, design review applied (`docs/DESIGN-REVIEW.md`). The demo replay is now a real voice call (`web/public/demo/call.json`, 115 s), recorded with `scripts/record_demo.py`.
- Phase 6 (code): signed Twilio webhook, single-use stream tokens, keypad linking to one tab, all tested with simulated Twilio messages.
- Phase 6 (softphone): a browser softphone calls the phone line through Twilio without a number (DECISIONS #34); `scripts/dev_server.py --phone` opens a quick tunnel and points the TwiML App at it. Trial account, API key and TwiML App set up. Not yet run end to end: the first real call through Twilio is the Phase 6 check, and it also shows whether a trial account allows `<Connect><Stream>`. The owner runs it; opening a public tunnel is not something the build agent does.
- Website QA (2026-10-03), through the real page with a synthetic Japanese caller and the clock at 15:00 Tokyo: the promise, handoff and hang-up paths all work end to end in the browser, and every control was clicked at 1440 and 390. Fixed: a blocked microphone used to open a call Kenji could not hear; connection errors read "ICE servers unavailable (502)" and "Offer request failed: [object Response]"; a finished, refused or replayed call had no way on; a summary chip on a phone hid its card under the sticky bars; a local call took 6 s to start (DECISIONS #35 to #37). Open: Kenji's line reaches the X-ray only when he finishes saying it, so a 20 s line shows nothing new while it plays.
- Owner's review (2026-10-03), all done and checked on live browser calls with a synthetic caller: a Hold button (DECISIONS #38; a 7 s pause on hold stayed one turn), Kenji's line shown as he starts it with 「はい、」 folded into the answer (#39), announcements before scripted steps dropped (#40), a subtitle that fails says so (#41), the transcript as a card with no scroll box inside the page (#42), the audit record as a timeline (#43), and a way home from every page. Real-model check after all of it: 24 of 24, twice.
- The demo replay is now a recorded voice call with sound on request (DECISIONS #44), recorded on the new code: Kenji's lines appear as he starts them.
- Five personas, the character card on screen with Say it, and the softphone's own transcript (DECISIONS #45 to #47), built in three parallel branches and merged one at a time. Checked: a live browser call as 田中けんた driven only by Say it reached a promise with his own figures; the real-model check passed 24 of 24 twice.
- Any-hour calls, 25 calls a day, Smart Turn as a second opinion on turn ends, a demo you can play, pause and scrub with both voices, and the caller's tone from SenseVoice (DECISIONS #48 to #52), built in parallel branches and merged one at a time. Checked: the real-model check passed 24 of 24; 620 Python tests, 118 web unit tests and 75 Playwright tests pass.
- A features page at `/features` (DECISIONS #53) for engineers, founders and hiring managers: how Kenji answers in about 0.7 s on a model that takes 2 to 6 s, how turn-taking works in Japanese, where each X-ray card's data comes from and what each library does, with real screenshots of the recorded call and scroll animation by GSAP. It is linked from the landing page's header. Checked: every claim on it against the repo, lint and types, 123 web unit tests, and the landing, accessibility and features browser tests on desktop and phone (50 passed).
- Deployed (2026-10-03), browser calls only, scaling to zero: the page and proxy on a Cloudflare Worker at https://call-kenji.call-kenji-web.workers.dev, the voice server on Cloud Run (project `call-kenji`, us-west1) with Cloudflare TURN for call audio, secrets in Secret Manager, a ₹1,700 (about $20) budget alert. Checked: the smoke test passes except the phone-webhook check (the phone line is off), and a full browser call on the public site through TURN reached a promise to pay. The GitHub deploy workflow still needs Workload Identity set up; this deploy was run by hand with the same settings.
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

1. One real browser call by a person, to hear Smart Turn and the caller's tone on a real voice.
2. Buy the Twilio number (owner approval: a US local number, $1.15 a month) and make the real phone-call check.
3. Deploy (owner approval), run the smoke test, one phone call and one browser call.
4. Fresh-clone check of the README and the hiring-manager review.

## Blockers

- Number purchase and public deploy need the owner's go-ahead.
- Local Windows: pnpm 10 cannot switch itself to the pinned pnpm 12, so use `npx pnpm@12.8.1` or `make PNPM="npx -y pnpm@12.8.1"`.
