"""Events the X-ray page receives for one call. This is the server-to-browser contract."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from kenji.domain.audit import JsonValue
from kenji.domain.compliance import CheckStatus
from kenji.domain.identity import IdentityStatus
from kenji.domain.outcome import CallOutcome
from kenji.domain.turn import TurnEndWait, TurnVerdict


class _Event(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CallStarted(_Event):
    type: Literal["call_started"] = "call_started"
    call_id: str
    transport: Literal["phone", "browser"]
    started_at: datetime
    # The persona the caller plays (content/personas.yaml); absent in older recordings.
    persona_id: str | None = None


class TranscriptLine(_Event):
    type: Literal["transcript"] = "transcript"
    line_id: str
    speaker: Literal["caller", "kenji"]
    ja: str
    is_final: bool
    is_backchannel: bool = False
    at: datetime


class Subtitle(_Event):
    type: Literal["subtitle"] = "subtitle"
    line_id: str
    en: str
    is_unavailable: bool = False


# How the caller's voice sounded on a turn, as a speech-emotion model hears it from the audio.
type CallerEmotion = Literal[
    "neutral", "happy", "sad", "angry", "fearful", "disgusted", "surprised", "unknown"
]
type CallerSound = Literal["laughter", "crying", "coughing", "sneezing"]


class CallerToneHeard(_Event):
    type: Literal["caller_tone"] = "caller_tone"
    line_id: str
    emotion: CallerEmotion
    sounds: list[CallerSound]


class FlowNodeEntered(_Event):
    type: Literal["flow_node"] = "flow_node"
    node: str


class TurnAssessed(_Event):
    type: Literal["turn"] = "turn"
    node: str
    utterance: str
    overlap_ms: float
    characters: int
    score: float
    threshold: float
    verdict: TurnVerdict


class TurnEndJudged(_Event):
    type: Literal["turn_end"] = "turn_end"
    # Smart Turn's reading of the caller's voice: how likely they had finished. None when it had
    # no pause to judge.
    finished_probability: float | None
    waited_for: TurnEndWait
    waited_ms: float


class StrategistUpdated(_Event):
    type: Literal["strategist"] = "strategist"
    identity: str
    situation: str
    ability_to_pay: str
    offers: list[str]
    next_move: str


class ComplianceUpdated(_Event):
    type: Literal["compliance"] = "compliance"
    calling_hours: CheckStatus
    identity_gate: CheckStatus
    offer_within_terms: CheckStatus
    ai_disclosure: CheckStatus
    recording_notice: CheckStatus
    # What the calling-hours rule means at the hour of this call; absent in older recordings.
    calling_hours_note: str = ""


# How Kenji opened his reply: scripted from the rules, with an instant 「はい、」 while the model
# worked, or with the model's own first words (older recordings).
type Opening = Literal["rules", "acknowledgement", "model"]


class LatencyMeasured(_Event):
    type: Literal["latency"] = "latency"
    turn: int
    end_of_turn_ms: float
    llm_first_token_ms: float
    tts_first_audio_ms: float
    total_ms: float
    p50_ms: float
    p95_ms: float
    budget_ms: float
    opened_with: Opening = "model"


class HandoffRecorded(_Event):
    type: Literal["handoff"] = "handoff"
    reason: str
    summary: str
    identity_status: IdentityStatus
    node: str
    requested_at: datetime


class SmsPreview(_Event):
    type: Literal["sms_preview"] = "sms_preview"
    ja: str
    en: str
    is_sent: Literal[False] = False


class CallEnded(_Event):
    type: Literal["call_ended"] = "call_ended"
    outcome: CallOutcome
    ended_at: datetime


class AuditPublished(_Event):
    type: Literal["audit"] = "audit"
    is_chain_valid: bool
    head_hash: str
    records: list[dict[str, JsonValue]]


CallEvent = Annotated[
    CallStarted
    | TranscriptLine
    | Subtitle
    | CallerToneHeard
    | FlowNodeEntered
    | TurnAssessed
    | TurnEndJudged
    | StrategistUpdated
    | ComplianceUpdated
    | LatencyMeasured
    | HandoffRecorded
    | SmsPreview
    | CallEnded
    | AuditPublished,
    Field(discriminator="type"),
]
