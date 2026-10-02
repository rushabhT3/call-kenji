import pytest

from kenji.domain.latency import (
    LATENCY_BUDGET_MS,
    TurnLatency,
    percentile,
    summarize_latency,
)


def _turn(total_ms: float) -> TurnLatency:
    return TurnLatency(
        end_of_turn_ms=total_ms / 2,
        llm_first_token_ms=total_ms / 4,
        tts_first_audio_ms=total_ms / 4,
    )


def test_total_is_the_sum_of_the_three_stages() -> None:
    latency = TurnLatency(end_of_turn_ms=400, llm_first_token_ms=550, tts_first_audio_ms=150)

    assert latency.total_ms == 1_100


def test_summary_reports_nearest_rank_p50_and_p95() -> None:
    latencies = [_turn(float(total)) for total in range(100, 2_100, 100)]

    summary = summarize_latency(latencies)

    assert summary is not None
    assert summary.turns == 20
    assert summary.p50_ms == 1_000
    assert summary.p95_ms == 1_900
    assert summary.budget_ms == LATENCY_BUDGET_MS
    assert summary.is_p50_within_budget


def test_slow_calls_exceed_the_budget() -> None:
    summary = summarize_latency([_turn(1_600), _turn(1_800)])

    assert summary is not None
    assert not summary.is_p50_within_budget


def test_no_turns_means_no_summary() -> None:
    assert summarize_latency([]) is None


def test_single_value_is_every_percentile() -> None:
    assert percentile([700.0], 0.0) == 700.0
    assert percentile([700.0], 1.0) == 700.0


@pytest.mark.parametrize(
    ("values", "fraction", "message"),
    [([], 0.5, "no values"), ([1.0], 1.5, "fraction")],
)
def test_percentile_rejects_bad_input(values: list[float], fraction: float, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        percentile(values, fraction)


def test_negative_components_are_rejected() -> None:
    with pytest.raises(ValueError, match="negative"):
        TurnLatency(end_of_turn_ms=-1, llm_first_token_ms=0, tts_first_audio_ms=0)
