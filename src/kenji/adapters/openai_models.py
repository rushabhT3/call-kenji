"""OpenAI behind the talker, strategist and translator ports.

Any OpenAI-compatible endpoint works through `base_url`, so switching provider is config.
"""

from typing import Any

from openai import AsyncOpenAI
from pipecat.services.llm_service import LLMService
from pipecat.services.openai.llm import OpenAILLMService


class OpenAITalker:
    def __init__(
        self, api_key: str, model: str, *, base_url: str | None, reasoning_effort: str | None
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._extra = {} if reasoning_effort is None else {"reasoning_effort": reasoning_effort}

    def create(self, system_instruction: str) -> LLMService[Any]:
        return OpenAILLMService(
            api_key=self._api_key,
            base_url=self._base_url,
            settings=OpenAILLMService.Settings(
                model=self._model,
                system_instruction=system_instruction,
                temperature=0.4,
                extra=dict(self._extra),
            ),
        )


class _ChatModel:
    def __init__(self, client: AsyncOpenAI, model: str, reasoning_effort: str | None) -> None:
        self._client = client
        self._model = model
        self._extra: dict[str, Any] = (
            {} if reasoning_effort is None else {"reasoning_effort": reasoning_effort}
        )

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
    def __init__(
        self, client: AsyncOpenAI, model: str, reasoning_effort: str | None, system_prompt: str
    ) -> None:
        super().__init__(client, model, reasoning_effort)
        self._system_prompt = system_prompt

    async def translate(self, japanese: str) -> str:
        return (await self._complete(self._system_prompt, japanese)).strip()
