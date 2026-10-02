# Versions

Pinned on 2026-10-02 after checking each registry.

Sources: the PyPI JSON API, the npm registry, the python.org release API, the nodejs.org dist index and the nodejs/Release schedule, and the GitHub releases API. "Released" is the registry upload date (UTC).

## Runtime

| Package | Version | Released | Docs | Notes |
| --- | --- | --- | --- | --- |
| CPython | **3.12.15** | 2026-09-30 | [python.org](https://www.python.org/downloads/release/python-31215/) | Pinned minor is 3.12 (see Notes). The latest stable CPython is 3.14.8 (2026-09-30). 3.15.0 is only at rc2, so it is excluded. |
| uv | **0.12.22** | 2026-10-02 | [docs.astral.sh/uv](https://docs.astral.sh/uv/) | The first uv release that can download CPython 3.12.15. The local uv 0.11.26 stops at 3.12.13. |
| Node.js | **24.21.0** (Krypton) | 2026-09-07 | [nodejs.org releases](https://nodejs.org/en/about/previous-releases) | Active LTS today. It moves to maintenance on 2026-10-20, and Node 26 becomes Active LTS on 2026-10-28. The current release line is 26.10.0, which is not LTS yet. Bundles npm 11.19.0. |
| pnpm | **12.8.1** | 2026-09-28 | [pnpm.io](https://pnpm.io/) | Set `"packageManager": "pnpm@12.8.1"`. Upgrade the local pnpm 10. The 12.x line has had 19 stable releases since 2026-08-26. |
| npm | 12.2.0 (latest) | 2026-09-30 | [docs.npmjs.com](https://docs.npmjs.com/) | Not needed because pnpm is the package manager. The npm 11.19.0 bundled with Node 24.21.0 is fine. npm 12 requires Node `^22.22.2 \|\| ^24.15.0 \|\| >=26`. |

## Python

Direct dependencies, declared in `pyproject.toml`:

| Package | Version | Released | Docs | Notes |
| --- | --- | --- | --- | --- |
| pipecat-ai | **1.12.0** | 2026-09-26 | [Quickstart](https://docs.pipecat.ai/pipecat/get-started/quickstart) · [Changelog](https://github.com/pipecat-ai/pipecat/blob/main/CHANGELOG.md) | Install as `pipecat-ai[soniox,cartesia,openai,webrtc,websocket,runner,tracing]==1.12.0`. `requires-python >=3.11`. Includes Flows (`pipecat.flows`). |
| fastapi | **0.142.2** | 2026-09-30 | [fastapi.tiangolo.com](https://fastapi.tiangolo.com/) | Also pulled in by the `websocket` and `runner` extras (`>=0.115.6,<1`). |
| uvicorn | **0.54.0** | 2026-09-25 | [uvicorn.dev](https://uvicorn.dev/) | The docs moved from uvicorn.org to uvicorn.dev. |
| pydantic | **2.13.5** | 2026-08-28 | [Pydantic docs](https://pydantic.dev/docs/validation/latest/get-started/) | The docs moved from docs.pydantic.dev to pydantic.dev/docs. |
| pydantic-settings | **2.15.0** | 2026-08-07 | [Settings management](https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/) | Typed config that fails fast at startup. |
| pyyaml | **6.0.3** | 2025-09-25 | [PyYAML docs](https://pyyaml.org/wiki/PyYAMLDocumentation) | Also a pipecat-ai base dependency (`>=6,<7`). |
| onnxruntime | **1.24.4** | 2026-03-17 | [ONNX Runtime Python API](https://onnxruntime.ai/docs/api/python/) | **Not the latest.** pipecat-ai 1.12.0 requires `onnxruntime~=1.24.3`, so 1.30.0 (2026-09-10) cannot be co-installed. It is used for Silero VAD, smart-turn v3 and the optional ONNX classifier. |
| numpy | **2.5.3** | 2026-09-06 | [numpy.org/doc](https://numpy.org/doc/stable/) | `requires-python >=3.12`. Compatible with numba 0.68.0 from pipecat-ai. |
| opentelemetry-sdk | **1.45.0** | 2026-09-25 | [OTel Python](https://opentelemetry.io/docs/languages/python/) · [Pipecat tracing](https://docs.pipecat.ai/api-reference/server/utilities/opentelemetry) | Also pulled in by the `tracing` extra (`>=1.33.0,<2`). |
| opentelemetry-exporter-otlp-proto-http | **1.45.0** | 2026-09-25 | [OTel exporters](https://opentelemetry.io/docs/languages/python/exporters/) | OTLP over HTTP, which hosted backends accept. The gRPC exporter in Pipecat's Jaeger example is not needed. |
| twilio | **9.11.2** | 2026-09-28 | [twilio-python](https://www.twilio.com/docs/libraries/reference/twilio-python/) · [Media Streams](https://www.twilio.com/docs/voice/media-streams) | For webhook signature validation (`RequestValidator`) and TwiML. `TwilioFrameSerializer` does not need it. |
| openai | **3.23.0** | 2026-10-01 | [openai-python](https://github.com/openai/openai-python) | Declared directly: the strategist and translator call Chat Completions with structured outputs. Also a pipecat-ai base dependency (`>=1.74.0,<4`). |

Development dependencies (the `dev` group):

| Package | Version | Released | Docs | Notes |
| --- | --- | --- | --- | --- |
| pytest | **9.1.1** | 2026-06-19 | [docs.pytest.org](https://docs.pytest.org/en/stable/) | |
| pytest-asyncio | **1.4.0** | 2026-05-26 | [pytest-asyncio](https://pytest-asyncio.readthedocs.io/en/stable/) | |
| pytest-cov | **7.1.0** | 2026-03-21 | [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/) | |
| ruff | **0.16.10** | 2026-10-01 | [docs.astral.sh/ruff](https://docs.astral.sh/ruff/) | |
| mypy | **2.4.0** | 2026-10-01 | [mypy docs](https://mypy.readthedocs.io/en/stable/) | Run in strict mode. |
| types-PyYAML | **6.0.12.20260906** | 2026-09-06 | [typeshed](https://github.com/python/typeshed) | Type stubs for pyyaml 6.0.x. |
| onnx | **1.23.1** | 2026-09-29 | [onnx.ai](https://onnx.ai/onnx/) | Builds the tiny model the ONNX classifier tests load. The test model targets IR 9 / opset 17, which onnxruntime 1.24 runs. |

Transitive dependencies, locked by `uv.lock` and not declared directly:

| Package | Version | Released | Docs | Notes |
| --- | --- | --- | --- | --- |
| pipecat-ai-prebuilt | 1.2.2 | 2026-09-25 | [pipecat-prebuilt](https://github.com/pipecat-ai/pipecat-prebuilt) | Pulled in by the `runner` extra. It **replaces `pipecat-ai-small-webrtc-prebuilt`**, whose last release was 2.5.0 on 2026-04-22. That repo was renamed to `pipecat-prebuilt` and now serves every transport. |
| websockets | 17.1 | 2026-08-26 | — | Used by the Soniox and Cartesia services. Their extras add no packages. |
| aiortc | 1.15.0 | 2026-07-13 | [SmallWebRTC transport](https://docs.pipecat.ai/api-reference/server/services/transport/small-webrtc) | Pulled in by the `webrtc` extra. |
| av | 17.1.0 | 2026-06-07 | — | aiortc 1.15.0 caps it at `av<18`, so the latest av (19.0.0, released 2026-09-29) is not used. |
| opencv-python-headless | 4.14.0.94 | 2026-07-28 | — | Pulled in by the `webrtc` extra. It is scheduled to leave that extra in pipecat-ai 2.0.0. |
| numba | 0.68.0 | 2026-09-30 | — | A pipecat-ai base dependency. |
| loguru | 0.7.3 | 2024-12-06 | [loguru](https://loguru.readthedocs.io/en/stable/) | A pipecat-ai base dependency (`~=0.7.3`). Pipecat's logging guide recommends it. See the logging note. |
| opentelemetry-instrumentation | 0.66b0 | 2026-09-25 | — | Pulled in by the `tracing` extra. The `b` suffix is how OTel contrib versions every release, and 0.66b0 is the latest. |
| starlette | 1.7.0 | 2026-09-23 | — | A FastAPI dependency. Its `TestClient` imports `httpx2` first and falls back to `httpx`. |
| httpx2 | 2.13.1 | 2026-09-23 | [pydantic/httpx2](https://github.com/pydantic/httpx2) | Pulled in by openai 3.x. |
| docopt | 0.6.2 | 2014-06-16 | — | Pulled in by `num2words`. It is the only sdist-only package in the tree. It is pure Python and builds without a compiler. |

Not used:

| Package | Version | Released | Docs | Notes |
| --- | --- | --- | --- | --- |
| pipecat-ai-flows | 1.4.0 (final) | 2026-07-05 | [Migrating from pipecat-ai-flows](https://docs.pipecat.ai/pipecat/migration/flows) | **Deprecated. Do not install.** It requires `pipecat-ai>=1.4.0,<1.5.0`, which conflicts with 1.12.0. Its repository is archived. |
| pipecat-ai-small-webrtc-prebuilt | 2.5.0 (final) | 2026-04-22 | — | Superseded by `pipecat-ai-prebuilt`. |
| python-json-logger | 4.2.0 | 2026-08-15 | [python-json-logger](https://nhairs.github.io/python-json-logger) | Not needed because loguru emits JSON natively. |
| structlog | 26.1.0 | 2026-06-06 | — | Not needed, for the same reason. |
| httpx | 0.28.1 | 2024-12-06 | — | Not needed: nothing in the app makes raw HTTP calls. openai 3.x brings `httpx2`. |
| soniox | 2.9.0 | 2026-08-11 | — | The vendor SDK. Pipecat's Soniox service talks to the WebSocket API directly. |
| cartesia | 4.2.0 | 2026-09-02 | — | The vendor SDK. Pipecat's Cartesia service talks to the WebSocket API directly. |

## JavaScript

| Package | Version | Released | Docs | Notes |
| --- | --- | --- | --- | --- |
| react | **19.3.0** | 2026-09-09 | [react.dev](https://react.dev/) | |
| react-dom | **19.3.0** | 2026-09-09 | [react.dev](https://react.dev/) | Peer: `react ^19.3.0`. |
| @types/react | **19.3.0** | 2026-09-09 | — | |
| @types/react-dom | **19.3.0** | 2026-09-09 | — | Peer: `@types/react ^19.3.0`. |
| vite | **8.3.2** | 2026-10-01 | [vite.dev/guide](https://vite.dev/guide/) | The 8.x line has been stable since 2026-03-12. Requires Node `^20.19.0 \|\| >=22.12.0`. |
| @vitejs/plugin-react | **6.1.1** | 2026-08-28 | [plugin-react](https://github.com/vitejs/vite-plugin-react/tree/main/packages/plugin-react) | Peer: `vite ^8.0.0`. |
| typescript | **6.0.3** | 2026-04-16 | [typescriptlang.org/docs](https://www.typescriptlang.org/docs/) | **Not the `latest` tag.** 7.0.2 (2026-07-08) is the native-compiler release, and it has no classic JS API. typescript-eslint 8.71.0 requires `typescript >=4.8.4 <6.1.0`, and installing 7.0.2 fails with ERESOLVE. |
| @pipecat-ai/client-js | **1.13.1** | 2026-09-04 | [JS SDK](https://docs.pipecat.ai/api-reference/client/js/overview) | The entry point is `PipecatClient`. |
| @pipecat-ai/client-react | **1.8.2** | 2026-08-25 | [React SDK](https://docs.pipecat.ai/api-reference/client/react/overview) | Peers: `@pipecat-ai/client-js *`, `react >=18`. |
| @pipecat-ai/small-webrtc-transport | **1.10.8** | 2026-09-15 | [Small WebRTC (client)](https://docs.pipecat.ai/api-reference/client/js/transports/small-webrtc) | Peer: `@pipecat-ai/client-js ~1.13.0`. |
| @playwright/test | **1.63.0** | 2026-09-04 | [playwright.dev](https://playwright.dev/docs/intro) | Requires Node `>=20`. |
| eslint | **10.11.0** | 2026-09-18 | [eslint.org/docs](https://eslint.org/docs/latest/) | Requires Node `^20.19.0 \|\| ^22.13.0 \|\| >=24`. |
| @eslint/js | **10.0.1** | 2026-02-06 | [eslint.org/docs](https://eslint.org/docs/latest/) | Peer: `eslint ^10.0.0`. |
| typescript-eslint | **8.71.0** | 2026-09-28 | [typescript-eslint.io](https://typescript-eslint.io/getting-started/) | Peers: `eslint ^8.57 \|\| ^9 \|\| ^10`, `typescript <6.1.0`. |
| eslint-plugin-react-hooks | **7.1.1** | 2026-04-17 | [react.dev reference](https://react.dev/reference/eslint-plugin-react-hooks) | Supports eslint 10. |
| eslint-plugin-react-refresh | **0.5.7** | 2026-09-14 | [GitHub](https://github.com/ArnaudBarre/eslint-plugin-react-refresh) | Peer: `eslint ^9 \|\| ^10`. |
| prettier | **3.9.9** | 2026-09-23 | [prettier.io/docs](https://prettier.io/docs/) | |
| vitest | **5.0.3** | 2026-09-30 | [vitest.dev/guide](https://vitest.dev/guide/) | The 5.x line has been stable since 2026-09-03. If a plugin lags behind, fall back to 4.1.11 (the `V4` tag). Requires Node `^22.12.0 \|\| ^24 \|\| >=26`. |
| globals | **17.13.0** | 2026-10-01 | [GitHub](https://github.com/sindresorhus/globals) | |
| @types/node | **24.19.1** | 2026-10-01 | — | Matches the Node 24 runtime. The `latest` tag is 26.6.4, which tracks Node 26. |
| @pipecat-ai/voice-ui-kit | 0.14.1 (not used) | 2026-09-28 | [Pipecat UI](https://docs.pipecat.ai/client/pipecat-ui) | **Not needed.** The docs say "Pipecat UI replaces Voice UI Kit". Pipecat UI is a shadcn registry (Tailwind 4, `base-nova` style) that is installed as source. The live page builds its own components from `docs/DESIGN.md` tokens on `@pipecat-ai/client-react` hooks. |

## CI actions

| Package | Version | Released | Docs | Notes |
| --- | --- | --- | --- | --- |
| actions/checkout | **v7** (v7.0.1) | 2026-07-20 | [GitHub](https://github.com/actions/checkout) | SHA `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| actions/setup-node | **v7** (v7.0.0) | 2026-07-14 | [GitHub](https://github.com/actions/setup-node) | SHA `820762786026740c76f36085b0efc47a31fe5020` |
| astral-sh/setup-uv | **v10.2.0** | 2026-09-21 | [GitHub](https://github.com/astral-sh/setup-uv) | **There is no `@v10` tag.** Releases have been immutable since v8.0.0, with no major or minor tags, so use `@v10.2.0` or SHA `c18668ad3cf93ea998bef934396af7bb5c839dc7`. Set `version: "0.12.22"`. |
| pnpm/action-setup | **v6** (v6.1.0) | 2026-09-05 | [GitHub](https://github.com/pnpm/action-setup) | 6.1.0 adds pnpm 12 support. SHA `ea17c68df8912ef543352723c149a84f56e3d413` |
| actions/upload-artifact | **v7** (v7.0.1) | 2026-04-10 | [GitHub](https://github.com/actions/upload-artifact) | SHA `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` |

## Language model API

The demo's provider. Any OpenAI-compatible endpoint works through `LLM_BASE_URL` (DECISIONS #18).

| Service | Model | Checked | Docs | Notes |
| --- | --- | --- | --- | --- |
| Meta Model API | **muse-spark-1.3-contributor** | 2026-10-02 | [Reasoning](https://dev.meta.ai/docs/reasoning) · [Chat Completions](https://dev.meta.ai/docs/protocols/chat-completions) | Base URL `https://api.meta.ai/v1`. Used for the talker, the strategist and the translator, with `reasoning_effort: minimal`. Contributor tier: $0.10 / $0.20 per million input / output tokens, and Meta may use the traffic to improve its models. See the note below. |

## Pipecat feature docs

| Topic | Docs |
| --- | --- |
| Soniox STT (`SonioxSTTService`) | https://docs.pipecat.ai/api-reference/server/services/stt/soniox |
| Cartesia TTS (`CartesiaTTSService`) | https://docs.pipecat.ai/api-reference/server/services/tts/cartesia |
| OpenAI LLM (`OpenAILLMService`) | https://docs.pipecat.ai/api-reference/server/services/llm/openai |
| Twilio Media Streams guide | https://docs.pipecat.ai/pipecat/telephony/twilio-websockets |
| `FastAPIWebsocketTransport` | https://docs.pipecat.ai/api-reference/server/services/transport/fastapi-websocket |
| `TwilioFrameSerializer` | https://docs.pipecat.ai/api-reference/server/services/serializers/twilio |
| `SmallWebRTCTransport` (server) | https://docs.pipecat.ai/api-reference/server/services/transport/small-webrtc |
| Pipecat Flows guide | https://docs.pipecat.ai/pipecat/flows/introduction |
| Pipecat Flows API reference | https://docs.pipecat.ai/api-reference/pipecat-flows/overview |
| Migrating from pipecat-ai-flows | https://docs.pipecat.ai/pipecat/migration/flows |
| Client JS SDK | https://docs.pipecat.ai/api-reference/client/js/overview |
| Client React SDK | https://docs.pipecat.ai/api-reference/client/react/overview |
| Small WebRTC (client transport) | https://docs.pipecat.ai/api-reference/client/js/transports/small-webrtc |
| OpenTelemetry tracing | https://docs.pipecat.ai/api-reference/server/utilities/opentelemetry |
| Development runner | https://docs.pipecat.ai/api-reference/server/utilities/runner/guide |
| `ParallelPipeline` | https://docs.pipecat.ai/api-reference/server/pipeline/parallel-pipeline |
| Silero VAD | https://docs.pipecat.ai/api-reference/server/services/vad/silero-vad-analyzer |
| Smart Turn | https://docs.pipecat.ai/api-reference/server/utilities/turn-detection/smart-turn-overview |
| Logging | https://docs.pipecat.ai/pipecat-cloud/fundamentals/logging |
| Docs index (machine-readable) | https://docs.pipecat.ai/llms.txt |

## Notes

### Python minor: 3.12

Pin `requires-python = "==3.12.*"` and `.python-version` = `3.12.15`.

- **Pipecat tests on 3.12.** Pipecat's full unit test suite (`.github/workflows/tests.yaml`) runs only on Python 3.12. Versions 3.11 through 3.14 get an import smoke test only (`python-compatibility.yaml`). The pipecat-ai package metadata has no Python version classifiers.
- **Pipecat deploys on 3.12.** `pipecat init` generates a Dockerfile that starts `FROM dailyco/pipecat-base:latest`. That image has the same digest as `latest-py3.12`.
- **All wheels exist on both platforms.** Every package in the tree has a wheel for cp312 on `win_amd64` and on `manylinux_2_28_x86_64`. This was checked by resolving with `uv pip compile --python-platform` for each target and then checking the wheel tags of all 126–127 pins. The only exception is `docopt`, which is pure Python. The same check passes for 3.13 and 3.14 with identical versions, so moving up later is a one-line change.
- **Windows smoke test passed.** Installing the 3.12 set on Windows imported cleanly. That covers `pipecat.flows` and the Soniox, Cartesia and OpenAI services. It also covers the Twilio serializer, the FastAPI WebSocket and SmallWebRTC transports, Silero, smart-turn v3, tracing setup, the runner, onnxruntime and both OTLP exporters.
- **Trade-off.** 3.12 gets security fixes only (until 2028-10). 3.14 is the upgrade path once Pipecat runs its test suite on it. It gets bug fixes until 2027-10 and security fixes until 2030-10.

### Flows ships inside pipecat-ai

- Since **pipecat-ai 1.5.0** (2026-07-04), Flows is part of the core package as `pipecat.flows`. Import it with `from pipecat.flows import FlowManager, NodeConfig, FlowsFunctionSchema, FlowArgs, FlowResult`.
- `pipecat-ai-flows` is deprecated. Its final release is 1.4.0, which requires `pipecat-ai<1.5.0`. The `pipecat-flows` repository is archived. If the old package is installed alongside Pipecat, Pipecat logs an error.
- Pipecat 1.9.0 added a declarative `FlowConfig` that describes a flow as YAML or JSON, with a schema at `pipecat/flows/flow_config.schema.json`. This is not the static `flow_config` parameter from the 0.0.x series, which was removed.

### Pipecat extras

```
pipecat-ai[soniox,cartesia,openai,webrtc,websocket,runner,tracing]==1.12.0
```

Each extra name appears as `Provides-Extra` in the 1.12.0 wheel's `METADATA`:

| Extra | Adds |
| --- | --- |
| `soniox`, `cartesia`, `openai` | Nothing. Their dependencies (`websockets`, `openai`) are already base dependencies. They are kept because they are the documented install pattern. |
| `webrtc` | `aiortc>=1.14.0,<2`, `opencv-python-headless>=4.11.0.86,<5` |
| `websocket` | `fastapi>=0.115.6,<1` |
| `runner` | `uvicorn>=0.32.0,<1`, `fastapi>=0.115.6,<1`, `pipecat-ai-prebuilt>=1.2.2` |
| `tracing` | `opentelemetry-sdk>=1.33.0,<2`, `opentelemetry-api>=1.33.0,<2`, `opentelemetry-instrumentation>=0.54b0,<1` |

Some features need no extra:

- **Silero VAD.** A `silero` extra exists but adds nothing, because `onnxruntime` is a base dependency and the model ships in the wheel.
- **Smart-turn v3.** `LocalSmartTurnAnalyzerV3` needs only onnxruntime, numpy and soxr, and the model `smart-turn-v3.2-cpu.onnx` is bundled.
- **The Twilio serializer.**

### Constraints that override "latest"

| Package | Pinned | Latest | Why |
| --- | --- | --- | --- |
| onnxruntime | 1.24.4 | 1.30.0 | pipecat-ai 1.12.0 declares `onnxruntime~=1.24.3`. The optional ONNX classifier must target the 1.24 runtime. |
| av | 17.1.0 (transitive) | 19.0.0 | aiortc 1.15.0 declares `av<18`. |
| typescript | 6.0.3 | 7.0.2 | typescript-eslint 8.71.0 declares `typescript <6.1.0`. |
| @types/node | 24.19.1 | 26.6.4 | Matches the Node 24 LTS runtime. |

### API changes to build against (pipecat-ai 1.12.0)

- **System prompt.** Putting the system prompt in a `"system"` message at the start of `LLMContext` was deprecated in 1.9.0 and stops working in 2.0.0. Pass `system_instruction=` to the LLM service instead. To change it at runtime, push `LLMUpdateSettingsFrame(LLMSettings(system_instruction=...))`.
- **Soniox STT.**
  - The default model is `stt-rt-v5`. Set the model through `settings=SonioxSTTService.Settings(model=...)`, because the `model=` constructor argument is deprecated.
  - `vad_force_turn_endpoint` defaults to `True`, which uses Pipecat's local VAD and smart-turn rather than Soniox endpointing.
- **Cartesia TTS.** The default model is `sonic-3.6`. The `cartesia_version` argument was deprecated in 1.8.0.
- **OpenAI LLM.** The default model is `gpt-4.1`. Set the model explicitly from config.
- **Twilio serializer.** `TwilioFrameSerializer` has `auto_hang_up=True` by default. That setting requires `call_sid`, `account_sid` and `auth_token`, and construction raises `ValueError` if any is missing.
- **Turn handling.**
  - `LLMSettings.filter_incomplete_user_turns` was deprecated in 1.7.0. Use `FilterIncompleteUserTurnStrategies` via `LLMUserAggregatorParams(user_turn_strategies=...)`.
  - Overriding `reset()` on turn strategies was deprecated in 1.6.0. Use `handle_user_turn_started()` and `handle_user_turn_stopped()`.
- **Scaffolding.** `pipecat create` was removed in 1.5.0. Use `pipecat init`.

### Muse Spark through the OpenAI-compatible API

The docs say Muse Spark always reasons. `reasoning_effort: "none"` returns HTTP 400, `"max"` is
for the standard tier only, and the contributor tier accepts `minimal`, `low`, `medium`, `high`
and `xhigh`. `logprobs`, `stop` and `n > 1` are not supported.

A probe against `muse-spark-1.3-contributor` on 2026-10-02 confirmed what the app relies on:

- **The `developer` role is accepted.** Flows task messages and the strategist's hint use it, so
  Pipecat's `OpenAILLMService` keeps `supports_developer_role = True`.
- **Strict structured output works.** `response_format` with `json_schema` and `strict: true`
  returned advice that the `Advice` model validated.
- **Tools are accepted on streamed requests.** A streamed request carrying a function tool was
  accepted and streamed its answer. The model chose to answer in text, so the probe did not see a
  streamed tool call; the real-model conversation tests cover that.
- **Effort levels.** `minimal` and `xhigh` were both accepted on the contributor tier.

### Tracing exporter

Pipecat's tracing extra does not include an exporter. The project uses the HTTP one; the docs show both:

- **gRPC:** `opentelemetry-exporter-otlp-proto-grpc`, for a local Jaeger or collector on `:4317`. Not used.
- **HTTP:** `opentelemetry-exporter-otlp-proto-http` (pinned above), for Langfuse, LangSmith, SigNoz and other hosted OTLP endpoints, configured through `OTEL_EXPORTER_OTLP_ENDPOINT` and `OTEL_EXPORTER_OTLP_HEADERS`.

Both are at 1.45.0. The `opentelemetry-exporter-otlp` meta-package installs both.

### Logging

Pipecat's logging guide recommends loguru, which is already a pinned dependency. Structured JSON logs need no extra package: `logger.add(sys.stdout, serialize=True)` writes one JSON object per line.

### HTTP client

No HTTP client is declared directly. openai 3.x depends on `httpx2` (pydantic's successor to httpx), and Starlette 1.7's `TestClient` prefers it.

### Node and local tooling

- **Node.** The local Node 22.16.0 satisfies every pinned package's engine range: vite needs `>=22.12`, eslint needs `^22.13`, vitest needs `^22.12` and Playwright needs `>=20`. CI and deployment should use 24.21.0 so that local and CI runtimes match.
- **Python and uv.** The local uv 0.11.26 can only install CPython 3.12.13. Run `uv self update` to get 0.12.22 before syncing with `.python-version` = `3.12.15`.
