# Deploying Call Kenji

Deploying costs money and puts the agent on the public internet, so every step below is run by a
person. The `Deploy` workflow is manual (`workflow_dispatch`) for the same reason.

## Shape

```
Browser ──HTTPS──▶ Cloudflare Worker ──┬─ static page (Workers static assets, free)
                                       └─ /api/*, /ws/* ──▶ Cloud Run: voice server (FastAPI + Pipecat)
Browser ◀──WebRTC media via Cloudflare TURN──▶ Cloud Run
Phone ──▶ Twilio ──webhook + Media Streams WebSocket──▶ Cloud Run
Cloud Run ──▶ Soniox (STT) · Cartesia (TTS) · language model API
Cloud Run ──▶ Cloud Storage volume at /data (transcripts, events, audit, counters; deleted after 30 days)
```

## Why Cloud Run and Cloudflare TURN, not Pipecat Cloud

Checked on 2026-10-02 against the providers' current docs and price pages:

- **One service holds everything the guardrails need.** That covers the signed Twilio webhook, the
  single-use stream tokens, the daily counters, the SmallWebRTC offer endpoints and the private
  viewer feed. Pipecat Cloud only exposes routes per running session, so the webhook and the
  counters would need a second host anyway.
- **Cost.** One always-warm Cloud Run instance (1 vCPU, 1 GiB, request-based billing) costs about
  $12 a month. A warm Pipecat Cloud agent costs about $48.60 a month at the same usage.
- **CPU stays allocated during calls.** Each live call holds a WebSocket open: the viewer feed for
  browser calls, the media stream for phone calls. Cloud Run counts an instance with an open
  WebSocket as active, so request-based billing still gives the call CPU.
- **TURN is free at this volume.** Cloud Run takes no inbound UDP, so browser media relays through
  Cloudflare TURN. The first 1,000 GB a month is free, and we use about 1 GB.
- **One instance only.** The WebRTC peer connections live in memory, so `--min-instances 1
  --max-instances 1` keeps every request for a call on the same instance.

Sources: Cloud Run pricing and WebSocket docs, Cloudflare Realtime TURN pricing, Pipecat Cloud pricing
and Session API docs. The links are in `docs/VERSIONS.md` and the vendor notes behind `docs/DECISIONS.md`.

## One-time setup

1. **Google Cloud** (project `PROJECT_ID`, region `us-west1`):
   - Enable Cloud Run, Cloud Build, Artifact Registry, Secret Manager and Cloud Storage.
   - Create the bucket `DATA_BUCKET` with a 30-day lifecycle delete rule. This is a backstop for
     the server's own purge.
   - Create these secrets: `llm-api-key`, `soniox-api-key`, `cartesia-api-key`,
     `twilio-auth-token`, `cloudflare-turn-api-token` and `proxy-shared-secret` (a long random
     string, for example `openssl rand -hex 32`).
   - Set up Workload Identity Federation for this GitHub repository, with a deploy service account.
2. **Budget alert at $20:**

   ```bash
   gcloud billing budgets create --billing-account=BILLING_ACCOUNT_ID \
     --display-name="call-kenji-20" --budget-amount=20USD \
     --threshold-rule=percent=0.5 --threshold-rule=percent=0.9 --threshold-rule=percent=1.0 \
     --threshold-rule=percent=1.0,basis=forecasted-spend \
     --filter-projects=projects/PROJECT_ID
   ```

   GCP budgets alert but do not stop spending. Cap each provider as well:
   - **Cartesia:** turn overage off, so requests fail once the plan's credits run out.
   - **Soniox:** set a monthly budget cap under the organisation's limits.
   - **Language model provider:** set a monthly spend limit.
   - **Twilio:** add a monthly usage trigger at $20.
3. **Cloudflare:**
   - Create a Realtime TURN key. Its ID goes in the repository variable `CLOUDFLARE_TURN_KEY_ID`;
     its API token goes in the secret above.
   - Create an API token that can deploy Workers.
4. **GitHub repository settings:**
   - Secrets: `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_DEPLOY_SERVICE_ACCOUNT`, `DATA_BUCKET`,
     `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`.
   - Variables: `LLM_BASE_URL`, `LLM_REASONING_EFFORT`, `TALKER_MODEL`, `STRATEGIST_MODEL`,
     `TRANSLATOR_MODEL`, `TWILIO_ACCOUNT_SID`, `PUBLIC_BASE_URL` (the Cloud Run URL),
     `CLOUDFLARE_TURN_KEY_ID`, `VOICE_SERVER_URL` (the Cloud Run URL), and `PHONE_NUMBER` (shown
     on the page).
5. **Worker secret:**
   - Run `npx wrangler@4.147.0 secret put PROXY_SHARED_SECRET`, using the same value as the GCP
     secret.
   - The voice server only trusts a forwarded visitor address when this value matches.
6. **Twilio:**
   - Buy the number. A Japanese number needs a corporate regulatory bundle; the cheapest number
     without documents is a US local number at $1.15 a month.
   - Point its voice webhook (HTTP POST) at `https://<cloud-run-url>/twilio/voice`.

## Deploy

Run the **Deploy** workflow from the Actions tab. It deploys the voice server to Cloud Run, then
builds the page and deploys the Worker.

## Smoke test after deploying

```bash
uv run python scripts/smoke.py https://<worker-domain>
```

The script checks the following:

- the page and the demo recording are served;
- `/api/health` answers through the Worker;
- `/api/ice` returns TURN credentials;
- `/ws/viewer` issues a four-digit code;
- an unsigned request to `/twilio/voice` is refused.

After that, make one phone call and one browser call.

## Monthly cost at 60 phone minutes and 30 browser minutes a day

| Item | Basis | $/month |
|---|---|---|
| Cloud Run, 1 warm instance | request-based billing, mostly idle | ~12 |
| Cloudflare TURN and Workers | well under the free tiers | 0 |
| Twilio US local number | | 1.15 |
| Twilio inbound voice | 1,800 min × $0.0085 | 15.30 |
| Twilio Media Streams | 1,800 min × $0.0044 | 7.92 |
| Soniox real-time STT | 45 h × $0.12 | 5.40 |
| Cartesia Sonic | about 324k characters a month | ~20 |
| Language model (Muse Spark contributor) | about 11k turns × ~5k tokens (talker, strategist, subtitles) at $0.10 / $0.20 per million | ~7 |
| **Total** | | **≈ $69** |

The guardrails cap usage: 5 minutes a call, 60 phone and 60 browser minutes a day, and 3 calls a
day per caller.
