"""A call the guardrails turn away still hears a polite line before the line closes."""

from pipecat.frames.frames import EndFrame, TTSSpeakFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineWorker
from pipecat.transports.base_transport import BaseTransport
from pipecat.workers.runner import WorkerRunner

from kenji.app.call_parts import CallIO
from kenji.app.events import CallStarted, Subtitle, TranscriptLine
from kenji.app.ports import Clock, TextToSpeechFactory
from kenji.app.script import Line, Lines
from kenji.app.session import CallContext
from kenji.domain.audit import AuditEntry
from kenji.domain.guardrails import Refusal


def refusal_line(lines: Lines, refusal: Refusal) -> Line:
    return {
        Refusal.DAILY_MINUTES_USED_UP: lines.daily_minutes_used_up,
        Refusal.CALLER_DAILY_LIMIT: lines.caller_daily_limit,
    }[refusal]


async def speak_and_hang_up(
    transport: BaseTransport, line: Line, text_to_speech: TextToSpeechFactory
) -> None:
    pipeline = Pipeline([transport.input(), text_to_speech.create(), transport.output()])
    worker = PipelineWorker(pipeline, enable_rtvi=False)

    async def on_connected(_transport: BaseTransport, _client: object) -> None:
        await worker.queue_frames([TTSSpeakFrame(line.ja), EndFrame()])

    transport.add_event_handler("on_client_connected", on_connected)
    runner = WorkerRunner(handle_sigint=False)
    await runner.add_workers(worker)
    await runner.run()


def publish_refusal(io: CallIO, context: CallContext, line: Line, clock: Clock) -> None:
    io.sink.publish(
        CallStarted(
            call_id=context.call_id,
            transport=context.transport,
            started_at=context.started_at,
            persona_id=context.persona_id,
        )
    )
    io.sink.publish(
        TranscriptLine(
            line_id="kenji-1", speaker="kenji", ja=line.ja, is_final=True, at=clock.now()
        )
    )
    io.sink.publish(Subtitle(line_id="kenji-1", en=line.en))
    io.audit.append(
        AuditEntry(
            kind="call_refused", recorded_at=clock.now().isoformat(), payload={"line": line.en}
        )
    )
