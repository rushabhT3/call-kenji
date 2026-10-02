"""What the caller sees after hanging up: outcome, SMS preview (never sent) and audit record."""

from kenji.app.agreement import describe_handoff_sms, describe_promise_sms
from kenji.app.call_parts import CallKit, CallParts
from kenji.app.events import AuditPublished, SmsPreview
from kenji.app.script import Line
from kenji.domain.audit import chain_head, verify_chain
from kenji.domain.contact import may_contact
from kenji.domain.outcome import CallOutcome, PaymentPromise, follow_up_sms_allowed


def _sms_for(outcome: CallOutcome, promise: PaymentPromise | None, kit: CallKit) -> Line | None:
    templates, debtor = kit.script.sms, kit.account.debtor
    if outcome is CallOutcome.PROMISE_TO_PAY and promise is not None:
        return describe_promise_sms(templates, promise.decision, debtor)
    if outcome is CallOutcome.HUMAN_HANDOFF:
        return describe_handoff_sms(templates, debtor)
    return None


def publish_debrief(kit: CallKit, parts: CallParts) -> CallOutcome:
    session, sink, audit = parts.session, parts.io.sink, parts.io.audit
    outcome = session.finish()
    contactable = may_contact(kit.contacts.preferences(), session.context.caller_ref)
    sms = _sms_for(outcome, session.promise, kit)
    if sms is not None and follow_up_sms_allowed(outcome, contactable):
        sink.publish(SmsPreview(ja=sms.ja, en=sms.en))
    records = audit.records()
    sink.publish(
        AuditPublished(
            is_chain_valid=verify_chain(records).is_valid,
            head_hash=chain_head(records),
            records=[record.to_json() for record in records],
        )
    )
    return outcome
