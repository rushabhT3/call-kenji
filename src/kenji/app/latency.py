"""Per-turn voice-to-voice latency, split into end of turn, LLM first token and TTS first audio."""

from kenji.app.events import LatencyMeasured
from kenji.app.ports import EventSink
from kenji.domain.latency import TurnLatency, summarize_latency

_MS_PER_SECOND = 1000.0


def split_turn_latency(
    end_of_turn_secs: float | None, llm_first_token_secs: float | None, total_secs: float
) -> TurnLatency | None:
    """Split a measured interval so the three stages sum exactly to the measured total.

    The TTS stage is what remains after end-of-turn and the LLM's first token: it covers
    sentence aggregation and the speech service's own time to first audio.
    """
    if end_of_turn_secs is None or llm_first_token_secs is None:
        return None
    end_of_turn_ms = end_of_turn_secs * _MS_PER_SECOND
    llm_ms = llm_first_token_secs * _MS_PER_SECOND
    remainder_ms = total_secs * _MS_PER_SECOND - end_of_turn_ms - llm_ms
    return TurnLatency(
        end_of_turn_ms=end_of_turn_ms,
        llm_first_token_ms=llm_ms,
        tts_first_audio_ms=max(0.0, remainder_ms),
    )


class LatencyTracker:
    def __init__(self, sink: EventSink) -> None:
        self._sink = sink
        self._turns: list[TurnLatency] = []

    def record(self, latency: TurnLatency) -> None:
        self._turns.append(latency)
        summary = summarize_latency(self._turns)
        if summary is None:
            return
        self._sink.publish(
            LatencyMeasured(
                turn=len(self._turns),
                end_of_turn_ms=latency.end_of_turn_ms,
                llm_first_token_ms=latency.llm_first_token_ms,
                tts_first_audio_ms=latency.tts_first_audio_ms,
                total_ms=latency.total_ms,
                p50_ms=summary.p50_ms,
                p95_ms=summary.p95_ms,
                budget_ms=summary.budget_ms,
            )
        )
