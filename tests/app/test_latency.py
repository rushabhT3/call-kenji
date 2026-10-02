"""Each turn is timed until the caller hears Kenji, with a note of what Kenji opened with."""

from typing import cast

from kenji.app.events import LatencyMeasured
from kenji.app.latency import LatencyTracker, split_turn_latency
from tests.conversation.harness import MemoryRecorder


def test_a_reply_that_waited_on_the_model_splits_into_three_stages() -> None:
    latency = split_turn_latency(0.6, 2.3, 3.5)

    assert latency is not None
    assert (latency.end_of_turn_ms, latency.llm_first_token_ms) == (600.0, 2300.0)
    assert round(latency.tts_first_audio_ms) == 600


def test_a_reply_that_did_not_wait_on_the_model_has_no_model_stage() -> None:
    latency = split_turn_latency(0.6, None, 1.1)

    assert latency is not None
    assert latency.llm_first_token_ms == 0.0
    assert round(latency.tts_first_audio_ms) == 500


def test_a_turn_without_an_end_of_turn_time_is_not_measured() -> None:
    assert split_turn_latency(None, None, 1.1) is None


def test_the_published_measurement_says_how_kenji_opened() -> None:
    recorder = MemoryRecorder()
    tracker = LatencyTracker(recorder)
    latency = split_turn_latency(0.6, None, 1.1)
    assert latency is not None

    tracker.record(latency, "rules")

    published = cast(LatencyMeasured, recorder.of_type("latency")[0])
    assert published.opened_with == "rules"
    assert round(published.total_ms) == 1100
