# Decisions

Choices the brief left open, recorded so reviewers can check the code against them.

| # | Question | Decision | Where it lives |
|---|----------|----------|----------------|
| 1 | ¥5,000 × 6 = ¥30,000 does not cover ¥35,000. Must a plan cover the balance? | Yes. A plan is a monthly amount; the schedule is `ceil(balance / monthly)` payments and the last one is the remainder. ¥5,000 a month needs 7 payments and is rejected. The smallest acceptable amount, rounded up to a speakable ¥1,000, is ¥6,000 × 5 + ¥5,000. | `domain/terms.py` |
| 2 | "First payment within 45 days" — from when? | From the day of the call, inclusive: a call on 2 Oct allows a first payment from 2 Oct to 16 Nov. | `domain/terms.py` |
| 3 | Is 21:00:00 inside "08:00 to 21:00"? | No. The window is `08:00 <= t < 21:00` Japan time (UTC+9, no DST), matching the usual reading of the night-time contact restriction. | `domain/calling_hours.py` |
| 4 | Recording notice vs "never store audio" | The notice says the call is kept **as a text transcript** for 30 days, not that it is recorded as audio (録音). | `content/script_ja.yaml` |
| 5 | Greeting vs "someone else answers: disclose nothing" | Before identity is verified Kenji uses only the neutral name 「みなと」 and never mentions debt, collection, the amount or the account. The full name みなと債権回収 is used only after verification. | `content/script_ja.yaml`, flows |
| 6 | Source of English subtitles | Scripted lines carry their English in the script file. Model-generated lines and caller lines are translated asynchronously by a small model behind a `Translator` port; subtitles may lag the Japanese by a moment and never delay speech. Demo mode replays recorded subtitles. | `app/`, `adapters/` |
| 7 | Browser calls have no cap in the brief | Browser calls share the guardrails: 5 minutes per call, 3 calls a day per browser (hashed client address), and a separate 60-minute daily pool. | config + `domain/` guardrails |
| 8 | Where reference screenshots live | Captures of third-party sites stay local (git-ignored) under `docs/design-refs/`; `DESIGN.md` records the URLs and measured values. | `.gitignore` |
| 9 | Prebuilt client vs custom page | The Pipecat prebuilt client is a development tool only. The shipped page is the custom React app using the Pipecat client SDK. | `web/` |
| 10 | Where Cloudflare Workers fits | Decided in the deploy phase with current pricing; the static page is the natural candidate. | `README.md` |
| 11 | Strength of the 4-digit link code | Generated with `secrets`, single use, expires after 10 minutes, and a call gets 3 wrong attempts before linking is disabled for that call. | link registry |
| 12 | `make` on Windows | GNU Make for Windows (`winget install ezwinports.make`) or WSL. CI runs on Ubuntu. | `README.md` |
| 13 | Linguistic rule data in code | Kana readings, the aizuchi lexicon and honorific suffixes are rules, so they live beside the pure functions in `domain/`. Everything Kenji says, and every prompt, lives in `content/script_ja.yaml`. | `domain/`, `content/` |
