"""Voice-to-voice latency per turn, measured against a 1,500 ms budget."""

import math
from collections.abc import Sequence
from dataclasses import dataclass

LATENCY_BUDGET_MS = 1_500.0


@dataclass(frozen=True, slots=True)
class TurnLatency:
    end_of_turn_ms: float
    llm_first_token_ms: float
    tts_first_audio_ms: float

    def __post_init__(self) -> None:
        if min(self.end_of_turn_ms, self.llm_first_token_ms, self.tts_first_audio_ms) < 0:
            raise ValueError(f"latency components cannot be negative: {self}")

    @property
    def total_ms(self) -> float:
        return self.end_of_turn_ms + self.llm_first_token_ms + self.tts_first_audio_ms


@dataclass(frozen=True, slots=True)
class LatencySummary:
    turns: int
    p50_ms: float
    p95_ms: float
    budget_ms: float

    @property
    def is_p50_within_budget(self) -> bool:
        return self.p50_ms <= self.budget_ms


def percentile(values: Sequence[float], fraction: float) -> float:
    if not values:
        raise ValueError("percentile of no values")
    if not 0.0 <= fraction <= 1.0:
        raise ValueError(f"fraction must be in [0, 1], got {fraction}")
    ordered = sorted(values)
    rank = max(1, math.ceil(fraction * len(ordered)))
    return ordered[rank - 1]


def summarize_latency(
    latencies: Sequence[TurnLatency], budget_ms: float = LATENCY_BUDGET_MS
) -> LatencySummary | None:
    if not latencies:
        return None
    totals = [latency.total_ms for latency in latencies]
    return LatencySummary(
        turns=len(totals),
        p50_ms=percentile(totals, 0.5),
        p95_ms=percentile(totals, 0.95),
        budget_ms=budget_ms,
    )
