"""Typed view of content/script_ja.yaml; a missing line fails at startup, not mid-call."""

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict


class _Content(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Line(_Content):
    ja: str
    en: str

    def fill(self, fields: Mapping[str, str]) -> "Line":
        return Line(ja=self.ja.format_map(fields), en=self.en.format_map(fields))


class Persona(_Content):
    servicer_neutral: str
    servicer_full: str
    agent_name: str
    debtor_honorific: str


class Lines(_Content):
    greeting: Line
    identity_retry: Line
    identity_locked: Line
    verified: Line
    third_party_callback: Line
    read_back: Line
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
    handoff: Line


class Prompts(_Content):
    talker_role: str
    strategist_hint: str
    strategist_system: str
    translator_system: str


class NodeContent(_Content):
    task: str


class NodeContents(_Content):
    verify_identity: NodeContent
    state_balance: NodeContent
    listen: NodeContent
    negotiate: NodeContent
    read_back: NodeContent
    close: NodeContent


class Script(_Content):
    persona: Persona
    lines: Lines
    sms: SmsTemplates
    prompts: Prompts
    nodes: NodeContents
