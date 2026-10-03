"""Soniox hears Japanese and proposes turn ends, Smart Turn checks them, Cartesia speaks kana."""

from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.processors.aggregators.llm_response_universal import LLMUserAggregatorParams
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.soniox.stt import SonioxContextObject, SonioxSTTService
from pipecat.transcriptions.language import Language
from pipecat.turns.user_start import BaseUserTurnStartStrategy
from pipecat.turns.user_turn_strategies import UserTurnStrategies

from kenji.app.turns import CallerHold, TurnEndListener, UnfinishedPhraseHold
from kenji.domain.kana import to_speech_kana
from kenji.domain.text import without_stray_latin_words

# Soniox's documented range is 500-3000 ms. 1.5 s is its voice-agent recommendation; the
# default sensitivity is kept, since cutting callers off is the failure that costs most.
MAX_ENDPOINT_DELAY_MS = 1500
# Pipecat closes a turn nothing has closed after this much silence. Soniox closes every turn
# it heard words in within the delay above, so this only ends a turn on Hold, or one opened by
# noise it heard no words in; Pipecat's 5 s default would cut a caller on Hold short.
TURN_STOP_WATCHDOG_SECS = 30.0


async def kana_for_speech(text: str, _aggregation_type: str) -> str:
    return to_speech_kana(without_stray_latin_words(text))


class SonioxSpeechToText:
    def __init__(self, api_key: str, model: str, vocabulary: list[str]) -> None:
        self._api_key = api_key
        self._model = model
        self._vocabulary = vocabulary

    def create(self) -> FrameProcessor:
        return SonioxSTTService(
            api_key=self._api_key,
            vad_force_turn_endpoint=False,
            settings=SonioxSTTService.Settings(
                model=self._model,
                language_hints=[Language.JA],
                language_hints_strict=True,
                context=SonioxContextObject(terms=self._vocabulary),
                max_endpoint_delay_ms=MAX_ENDPOINT_DELAY_MS,
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


class SonioxEndpointTurnDetection:
    """Silero VAD hears speech start at once; Soniox's semantic endpointing proposes turn ends.

    A silence timer cut callers off at the pause in 「生年月日は、」. Soniox judges the end from
    the words, rhythm and intonation together, and UnfinishedPhraseHold waits longer when the
    words still stop on a particle, or when Smart Turn v3, Pipecat's bundled ONNX model, hears
    from the voice that the caller paused mid-sentence.
    """

    def user_params(
        self,
        start: BaseUserTurnStartStrategy,
        caller_hold: CallerHold,
        on_turn_end: TurnEndListener,
    ) -> LLMUserAggregatorParams:
        stop = UnfinishedPhraseHold(
            caller_hold=caller_hold, smart_turn=LocalSmartTurnAnalyzerV3, on_turn_end=on_turn_end
        )
        return LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer(),
            user_turn_strategies=UserTurnStrategies(start=[start], stop=[stop]),
            user_turn_stop_timeout=TURN_STOP_WATCHDOG_SECS,
        )
