"""Typed view of content/script_ja.yaml; a missing line fails at startup, not mid-call."""

import re
from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator

from kenji.domain.turn import TurnPolicy


class _Content(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Line(_Content):
    ja: str
    en: str

    @field_validator("ja")
    @classmethod
    def _join_japanese_lines(cls, value: str) -> str:
        # Folded YAML joins lines with ASCII spaces; Japanese needs none. A full-width
        # space (U+3000) written in the script is intentional and kept.
        return re.sub(r"[ \t\n]+", "", value)

    def fill(self, fields: Mapping[str, str]) -> "Line":
        return Line(ja=self.ja.format_map(fields), en=self.en.format_map(fields))


class Persona(_Content):
    servicer_neutral: str
    servicer_full: str
    agent_name: str


class Lines(_Content):
    greeting: Line
    identity_locked: Line
    balance_statement: Line
    third_party_callback: Line
    read_back: Line
    read_back_single: Line
    promise_close: Line
    handoff_close: Line
    stop_contact_close: Line
    no_agreement_close: Line
    outside_calling_hours: Line
    daily_minutes_used_up: Line
    caller_daily_limit: Line
    time_up: Line


class SmsTemplates(_Content):
    promise: Line
    promise_single: Line
    handoff: Line


class Prompts(_Content):
    talker_role: str
    strategist_hint: str
    strategist_system: str
    translator_system: str


class NodeContent(_Content):
    task: str
    min_interruption_score: float = Field(gt=0.0, le=1.0)

    @property
    def turn_policy(self) -> TurnPolicy:
        return TurnPolicy(min_interruption_score=self.min_interruption_score)


class NodeContents(_Content):
    greeting: NodeContent
    verify_identity: NodeContent
    state_balance: NodeContent
    listen: NodeContent
    negotiate: NodeContent
    read_back: NodeContent


class ToolContent(_Content):
    description: str
    parameters: dict[str, str]


class ToolContents(_Content):
    verify_identity: ToolContent
    third_party_answered: ToolContent
    get_account_summary: ToolContent
    check_terms: ToolContent
    confirm_plan: ToolContent
    record_promise: ToolContent
    request_human: ToolContent
    record_stop_contact: ToolContent
    end_without_agreement: ToolContent


class Script(_Content):
    persona: Persona
    lines: Lines
    sms: SmsTemplates
    prompts: Prompts
    nodes: NodeContents
    tools: ToolContents
