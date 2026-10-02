"""Soniox for Japanese speech-to-text, Cartesia for Japanese speech with kana readings."""

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.processors.aggregators.llm_response_universal import LLMUserAggregatorParams
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.soniox.stt import SonioxContextObject, SonioxSTTService
from pipecat.transcriptions.language import Language
from pipecat.turns.user_start import BaseUserTurnStartStrategy
from pipecat.turns.user_turn_strategies import UserTurnStrategies

from kenji.domain.kana import to_speech_kana


async def kana_for_speech(text: str, _aggregation_type: str) -> str:
    return to_speech_kana(text)


class SonioxSpeechToText:
    def __init__(self, api_key: str, model: str, vocabulary: list[str]) -> None:
        self._api_key = api_key
        self._model = model
        self._vocabulary = vocabulary

    def create(self) -> FrameProcessor:
        return SonioxSTTService(
            api_key=self._api_key,
            settings=SonioxSTTService.Settings(
                model=self._model,
                language_hints=[Language.JA],
                language_hints_strict=True,
                context=SonioxContextObject(terms=self._vocabulary),
            ),
        )


class CartesiaTextToSpeech:
    def __init__(self, api_key: str, model: str, voice_id: str) -> None:
        self._api_key = api_key
        self._model = model
        self._voice_id = voice_id

    def create(self) -> FrameProcessor:
        return CartesiaTTSService(
            api_key=self._api_key,
            settings=CartesiaTTSService.Settings(
                model=self._model, voice=self._voice_id, language=Language.JA
            ),
            text_transforms=[("*", kana_for_speech)],
        )


class SileroSmartTurnDetection:
    """Silero VAD for speech onset; Pipecat's default smart-turn model decides turn ends."""

    def user_params(self, start: BaseUserTurnStartStrategy) -> LLMUserAggregatorParams:
        return LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer(), user_turn_strategies=UserTurnStrategies(start=[start])
        )
