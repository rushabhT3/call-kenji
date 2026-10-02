"""Events the X-ray page receives for one call. This is the server-to-browser contract."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from kenji.domain.compliance import CheckStatus
from kenji.domain.identity import IdentityStatus
from kenji.domain.outcome import CallOutcome
from kenji.domain.turn import TurnVerdict


class _Event(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CallStarted(_Event):
    type: Literal["call_started"] = "call_started"
    call_id: str
    transport: Literal["phone", "browser"]
    started_at: datetime


class TranscriptLine(_Event):
    type: Literal["transcript"] = "transcript"
    line_id: str
    speaker: Literal["caller", "kenji"]
    ja: str
    is_final: bool
    at: datetime


class Subtitle(_Event):
    type: Literal["subtitle"] = "subtitle"
    line_id: str
    en: str


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
    verdict: TurnVerdict


class StrategistAdvice(_Event):
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
    records: list[dict[str, object]]


CallEvent = Annotated[
    CallStarted
    | TranscriptLine
    | Subtitle
    | FlowNodeEntered
    | TurnAssessed
    | StrategistAdvice
    | ComplianceUpdated
    | LatencyMeasured
    | HandoffRecorded
    | SmsPreview
    | CallEnded
    | AuditPublished,
    Field(discriminator="type"),
]
