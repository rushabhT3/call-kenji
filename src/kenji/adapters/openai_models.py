"""OpenAI-compatible chat completions behind the talker, strategist and translator ports.

Any OpenAI-compatible endpoint works through `base_url`, so switching provider is config:
OpenAI by default, or for example Meta's Muse Spark at https://api.meta.ai/v1.
"""

from dataclasses import dataclass
from functools import partial
from typing import Any, cast

from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletionChunk
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.services.llm_service import LLMService
from pipecat.services.openai.llm import OpenAILLMService

from kenji.adapters.hedging import first_to_start

# Muse Spark's first token: median about 2.3 s, with spikes past 15 s. A second request after
# the median trims that tail, and the duplicate input costs about $0.10 per million tokens.
HEDGE_AFTER_SECS = 2.5


@dataclass(frozen=True, slots=True)
class ChatEndpoint:
    api_key: str
    base_url: str | None
    reasoning_effort: str | None
    temperature: float | None

    def extra_options(self) -> dict[str, Any]:
        options: dict[str, Any] = {}
        if self.reasoning_effort is not None:
            options["reasoning_effort"] = self.reasoning_effort
        if self.temperature is not None:
            options["temperature"] = self.temperature
        return options

    def client(self) -> AsyncOpenAI:
        return AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)


class HedgedOpenAILLMService(OpenAILLMService):
    """Asks again when an answer is slow to start, and speaks whichever starts first."""

    hedge_after_secs: float = HEDGE_AFTER_SECS

    async def get_chat_completions(self, context: LLMContext) -> AsyncStream[ChatCompletionChunk]:
        start = partial(super().get_chat_completions, context)
        stream = await first_to_start(start, self.hedge_after_secs)
        # Pipecat only iterates the stream and closes it, which the hedged stream supports.
        return cast(AsyncStream[ChatCompletionChunk], stream)


class OpenAITalker:
    def __init__(self, endpoint: ChatEndpoint, model: str) -> None:
        self._endpoint = endpoint
        self._model = model

    def create(self, system_instruction: str) -> LLMService[Any]:
        return HedgedOpenAILLMService(
            api_key=self._endpoint.api_key,
            base_url=self._endpoint.base_url,
            settings=OpenAILLMService.Settings(
                model=self._model,
                system_instruction=system_instruction,
                extra=self._endpoint.extra_options(),
            ),
        )


class _ChatModel:
    def __init__(self, endpoint: ChatEndpoint, model: str) -> None:
        self._client = endpoint.client()
        self._model = model
        self._extra = endpoint.extra_options()

    async def _complete(self, system_prompt: str, user_text: str, **options: Any) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            **self._extra,
            **options,
        )
        content: str | None = response.choices[0].message.content
        if not content:
            raise ValueError(f"{self._model} returned an empty completion")
        return content


class OpenAIAdviceModel(_ChatModel):
    async def advise(
        self, system_prompt: str, conversation: str, json_schema: dict[str, Any]
    ) -> str:
        return await self._complete(
            system_prompt,
            conversation,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "advice", "strict": True, "schema": json_schema},
            },
        )


class OpenAITranslator(_ChatModel):
    def __init__(self, endpoint: ChatEndpoint, model: str, system_prompt: str) -> None:
        super().__init__(endpoint, model)
        self._system_prompt = system_prompt

    async def translate(self, japanese: str) -> str:
        return (await self._complete(self._system_prompt, japanese)).strip()
