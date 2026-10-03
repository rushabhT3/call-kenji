"""Each caller turn's audio is kept and heard once, beside the call and never in front of it."""

import threading

import pytest
from pipecat.frames.frames import Frame, InputAudioRawFrame
from pipecat.tests.utils import run_test

from kenji.app.caller_tone import (
    LEAD_IN_SECS,
    MAX_TURN_SECS,
    TURN_AUDIO_SAMPLE_RATE,
    CallerToneListener,
    TurnAudioRecorder,
)
from kenji.app.events import CallerToneHeard
from kenji.app.ports import CallerTone, TurnAudio
from tests.conversation.doubles import ANGRY_AND_LAUGHING, FixedToneClassifier, MemoryRecorder

FRAMES_PER_SEC = 50
TURN = "今月は少し厳しいです。"


def _microphone(seconds: float, sample_rate: int = TURN_AUDIO_SAMPLE_RATE) -> list[Frame]:
    frame_bytes = sample_rate // FRAMES_PER_SEC * 2
    return [
        InputAudioRawFrame(audio=bytes(frame_bytes), sample_rate=sample_rate, num_channels=1)
        for _ in range(round(seconds * FRAMES_PER_SEC))
    ]


def _audio(seconds: float) -> TurnAudio:
    return TurnAudio(pcm=bytes(int(seconds * TURN_AUDIO_SAMPLE_RATE) * 2), sample_rate=16_000)


class FailingClassifier:
    def classify(self, audio: TurnAudio) -> CallerTone:
        raise RuntimeError(f"model failed on {audio.seconds}s")


class StuckClassifier:
    def __init__(self) -> None:
        self.release = threading.Event()

    def classify(self, audio: TurnAudio) -> CallerTone:
        self.release.wait(timeout=5)
        raise RuntimeError(f"gave up on {audio.seconds}s")


async def test_a_turn_keeps_the_moment_before_it_was_noticed() -> None:
    recorder = TurnAudioRecorder()

    await run_test(recorder, frames_to_send=_microphone(2.0))

    assert recorder.take_turn_audio().seconds == LEAD_IN_SECS


async def test_a_turn_keeps_everything_the_caller_says_in_it() -> None:
    recorder = TurnAudioRecorder()
    recorder.start_turn()

    await run_test(recorder, frames_to_send=_microphone(2.0))

    assert recorder.take_turn_audio().seconds == 2.0


async def test_a_long_turn_keeps_its_latest_seconds() -> None:
    recorder = TurnAudioRecorder()
    recorder.start_turn()

    await run_test(recorder, frames_to_send=_microphone(MAX_TURN_SECS + 1.0))

    assert recorder.take_turn_audio().seconds == MAX_TURN_SECS


async def test_phone_audio_is_kept_at_the_rate_speech_models_take() -> None:
    recorder = TurnAudioRecorder()
    recorder.start_turn()

    await run_test(recorder, frames_to_send=_microphone(1.0, sample_rate=8_000))
    audio = recorder.take_turn_audio()

    assert audio.sample_rate == TURN_AUDIO_SAMPLE_RATE
    assert audio.seconds == pytest.approx(1.0, abs=0.1)


async def test_a_finished_turn_is_not_kept_for_the_next() -> None:
    recorder = TurnAudioRecorder()
    recorder.start_turn()
    await run_test(recorder, frames_to_send=_microphone(1.0))

    recorder.take_turn_audio()

    assert recorder.take_turn_audio().seconds == 0.0


async def test_the_callers_audio_still_reaches_speech_recognition() -> None:
    downstream, _ = await run_test(TurnAudioRecorder(), frames_to_send=_microphone(0.1))

    assert sum(isinstance(frame, InputAudioRawFrame) for frame in downstream) == 5


async def test_a_turn_is_heard_once_and_shown_on_its_own_line() -> None:
    classifier, sink = FixedToneClassifier(), MemoryRecorder()

    tone = await CallerToneListener(classifier, sink).hear("caller-3", TURN, _audio(2.0))

    assert tone == ANGRY_AND_LAUGHING
    assert len(classifier.heard) == 1
    assert sink.events == [
        CallerToneHeard(line_id="caller-3", emotion="angry", sounds=["laughter"])
    ]


@pytest.mark.parametrize(
    ("utterance", "seconds"),
    [("はい。", 2.0), ("うん", 2.0), (TURN, 0.2)],
    ids=["aizuchi", "short aizuchi", "too little audio"],
)
async def test_a_turn_too_short_to_hear_a_tone_in_is_skipped(
    utterance: str, seconds: float
) -> None:
    classifier, sink = FixedToneClassifier(), MemoryRecorder()

    tone = await CallerToneListener(classifier, sink).hear("caller-3", utterance, _audio(seconds))

    assert tone is None
    assert classifier.heard == []
    assert sink.events == []


async def test_a_failing_model_leaves_the_turn_unheard() -> None:
    sink = MemoryRecorder()
    listener = CallerToneListener(FailingClassifier(), sink)

    assert await listener.hear("caller-3", TURN, _audio(2.0)) is None
    assert sink.events == []


async def test_a_stuck_model_is_not_waited_for() -> None:
    classifier, sink = StuckClassifier(), MemoryRecorder()
    listener = CallerToneListener(classifier, sink, timeout_secs=0.05)

    tone = await listener.hear("caller-3", TURN, _audio(2.0))
    classifier.release.set()

    assert tone is None
    assert sink.events == []
