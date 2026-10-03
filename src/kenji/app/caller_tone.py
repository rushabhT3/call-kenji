"""How the caller sounds: each finished turn's audio is heard for emotion and sounds like laughter.

Words alone miss a caller who is upset or laughing it off. A speech-emotion model hears the
turn's audio once the turn has ended, in a worker thread beside the conversation: Kenji's reply
never waits for it. The strategist's advice on that turn waits a few seconds at most, so it can
take the tone into account. A slow or failed model leaves the call as it is.
"""

import asyncio

from loguru import logger
from pipecat.audio.utils import create_stream_resampler
from pipecat.frames.frames import Frame, InputAudioRawFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from kenji.app.events import CallerToneHeard
from kenji.app.ports import CallerEmotionClassifier, CallerTone, EventSink, TurnAudio
from kenji.domain.text import count_spoken_characters

TURN_AUDIO_SAMPLE_RATE = 16_000
# A turn is noticed only after its first syllables: the voice detector waits for speech to
# settle, and speech over Kenji counts once its words are heard. The second before is kept.
LEAD_IN_SECS = 1.0
# A caller on Hold can talk for minutes; the latest seconds say how they sound now.
MAX_TURN_SECS = 15.0
# Aizuchi such as はい or うん say too little to hear a tone in.
MIN_TONE_CHARACTERS = 3
MIN_TONE_SECS = 0.5
TONE_TIMEOUT_SECS = 3.0
_BYTES_PER_SAMPLE = 2


def _bytes_for(seconds: float) -> int:
    return int(seconds * TURN_AUDIO_SAMPLE_RATE) * _BYTES_PER_SAMPLE


class TurnAudioRecorder(FrameProcessor):
    """Keeps the caller's audio for the turn in progress, at the rate speech models take."""

    def __init__(self) -> None:
        super().__init__()
        self._resampler = create_stream_resampler()
        self._audio = bytearray()
        self._lead_in_bytes = _bytes_for(LEAD_IN_SECS)
        self._max_turn_bytes = _bytes_for(MAX_TURN_SECS)
        self._is_in_turn = False

    def start_turn(self) -> None:
        self._is_in_turn = True

    def take_turn_audio(self) -> TurnAudio:
        audio = TurnAudio(pcm=bytes(self._audio), sample_rate=TURN_AUDIO_SAMPLE_RATE)
        self._audio.clear()
        self._is_in_turn = False
        return audio

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        if isinstance(frame, InputAudioRawFrame):
            self._keep(
                await self._resampler.resample(
                    frame.audio, frame.sample_rate, TURN_AUDIO_SAMPLE_RATE
                )
            )
        await self.push_frame(frame, direction)

    def _keep(self, pcm: bytes) -> None:
        self._audio += pcm
        limit = self._max_turn_bytes if self._is_in_turn else self._lead_in_bytes
        if len(self._audio) > limit:
            del self._audio[: len(self._audio) - limit]


class CallerToneListener:
    """Hears how each caller turn sounded and shows it on that turn's transcript line."""

    def __init__(
        self,
        classifier: CallerEmotionClassifier,
        sink: EventSink,
        timeout_secs: float = TONE_TIMEOUT_SECS,
    ) -> None:
        self._classifier = classifier
        self._sink = sink
        self._timeout_secs = timeout_secs

    async def hear(self, line_id: str, utterance: str, audio: TurnAudio) -> CallerTone | None:
        if count_spoken_characters(utterance) < MIN_TONE_CHARACTERS or (
            audio.seconds < MIN_TONE_SECS
        ):
            return None
        tone = await self._classify(line_id, audio)
        if tone is not None:
            self._sink.publish(
                CallerToneHeard(line_id=line_id, emotion=tone.emotion, sounds=list(tone.sounds))
            )
        return tone

    async def _classify(self, line_id: str, audio: TurnAudio) -> CallerTone | None:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._classifier.classify, audio), self._timeout_secs
            )
        except TimeoutError:
            logger.warning(
                "caller tone timed out", line_id=line_id, timeout_secs=self._timeout_secs
            )
        except Exception:
            logger.exception("caller tone failed; the call continues without it", line_id=line_id)
        return None
