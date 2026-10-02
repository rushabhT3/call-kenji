"""Assemble and run one call.

transport -> STT -> turn handling -> Flows talker (+ strategist hint) -> kana TTS -> transport
"""

import asyncio
import time
from dataclasses import dataclass, replace

from loguru import logger
from pipecat.flows import FlowManager, NodeConfig
from pipecat.frames.frames import EndFrame, TTSSpeakFrame
from pipecat.observers.user_bot_latency_observer import LatencyBreakdown, UserBotLatencyObserver
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    AssistantTurnStoppedMessage,
    LLMAssistantAggregator,
    LLMContextAggregatorPair,
    LLMUserAggregator,
    LLMUserAggregatorParams,
    UserTurnStoppedMessage,
)
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.transports.base_transport import BaseTransport
from pipecat.turns.user_mute.first_speech_user_mute_strategy import (
    FirstSpeechUserMuteStrategy,
)
from pipecat.workers.runner import WorkerRunner

from kenji.app.call_parts import CallIO, CallKit, CallParts, build_call_parts
from kenji.app.debrief import publish_debrief
from kenji.app.events import CallStarted, TurnAssessed
from kenji.app.fast_path import Acknowledgement, FastPath
from kenji.app.latency import split_turn_latency
from kenji.app.observers import InterimTranscriptObserver
from kenji.app.session import CallContext
from kenji.app.strategist import count_caller_turns
from kenji.app.turns import AnswerWatch, BackchannelTurnStartStrategy, Floor
from kenji.domain.outcome import CallOutcome
from kenji.domain.turn import TurnDecision, TurnVerdict

IDLE_TIMEOUT_SECS = 45


@dataclass(frozen=True, slots=True)
class CallSetup:
    context: CallContext
    io: CallIO
    max_seconds: int
    input_processors: tuple[FrameProcessor, ...] = ()


class Call:
    def __init__(self, kit: CallKit, setup: CallSetup, transport: BaseTransport) -> None:
        self._kit = kit
        self._transport = transport
        self._max_seconds = setup.max_seconds
        self._input_processors = setup.input_processors
        self._parts: CallParts = build_call_parts(kit, setup.context, setup.io)
        self._floor = Floor()
        self._fast_path = self._build_fast_path()
        self._talker = kit.voice.talker.create(self._parts.talker_instruction)
        self._context = LLMContext()
        self._pair = LLMContextAggregatorPair(self._context, user_params=self._user_params())
        self._caller_heard_since: float | None = None
        self._worker = self._build_worker()
        self._flow_manager = FlowManager(
            worker=self._worker,
            llm=self._talker,
            context_aggregator=self._pair,
            global_functions=self._parts.flow.global_functions(),
        )
        self._wire_events()

    async def run(self) -> CallOutcome:
        session = self._parts.session
        self._parts.io.sink.publish(
            CallStarted(
                call_id=session.context.call_id,
                transport=session.context.transport,
                started_at=session.context.started_at,
            )
        )
        session.publish_compliance()
        timer = asyncio.create_task(self._end_at_time_limit())
        try:
            runner = WorkerRunner(handle_sigint=False)
            await runner.add_workers(self._worker)
            await runner.run()
        finally:
            timer.cancel()
            await self._parts.feed.drain()
        return publish_debrief(self._kit, self._parts)

    def _user_params(self) -> LLMUserAggregatorParams:
        params = self._kit.voice.turn_detection.user_params(self._turn_strategy())
        # The opening carries the AI disclosure; the caller is heard again once it has played.
        mute = FirstSpeechUserMuteStrategy()  # type: ignore[no-untyped-call]
        return replace(params, user_mute_strategies=[mute])

    def _turn_strategy(self) -> BackchannelTurnStartStrategy:
        return BackchannelTurnStartStrategy(
            classifier=self._kit.classifier,
            policy=self._parts.flow.turn_policy,
            on_decision=self._publish_turn,
            floor=self._floor,
        )

    def _build_fast_path(self) -> FastPath:
        lines = self._kit.script.lines
        acknowledgement = Acknowledgement(
            lines.acknowledgement.ja,
            self._floor,
            on_spoken=self._parts.feed.kenji_said,
            holding=lines.holding.ja,
            apology=lines.answer_failed.ja,
        )
        return FastPath(self._parts.planner, acknowledgement, set_node=self._set_node)

    def _build_worker(self) -> PipelineWorker:
        voice = self._kit.voice
        processors: list[FrameProcessor] = [
            self._transport.input(),
            *self._input_processors,
            voice.speech_to_text.create(),
            self._pair.user(),
            self._fast_path,
            self._parts.injector,
            self._talker,
            AnswerWatch(self._floor),
            voice.text_to_speech.create(),
            self._transport.output(),
            self._pair.assistant(),
        ]
        latency = UserBotLatencyObserver()
        latency.add_event_handler("on_latency_breakdown", self._on_latency)
        return PipelineWorker(
            Pipeline(processors),
            params=PipelineParams(enable_metrics=True, enable_usage_metrics=True),
            observers=[latency, InterimTranscriptObserver(self._parts.feed.caller_partial)],
            idle_timeout_secs=IDLE_TIMEOUT_SECS,
            enable_tracing=True,
            conversation_id=self._parts.session.context.call_id,
        )

    def _wire_events(self) -> None:
        self._transport.add_event_handler("on_client_connected", self._on_connected)
        self._transport.add_event_handler("on_client_disconnected", self._on_disconnected)
        self._pair.user().add_event_handler("on_user_mute_stopped", self._on_caller_heard_again)
        self._pair.user().add_event_handler("on_user_turn_started", self._on_user_turn_started)
        self._pair.user().add_event_handler("on_user_turn_stopped", self._on_user_turn_stopped)
        self._pair.assistant().add_event_handler(
            "on_assistant_turn_stopped", self._on_assistant_turn_stopped
        )

    async def _set_node(self, node: NodeConfig) -> None:
        await self._flow_manager.set_node_from_config(node)

    async def _on_connected(self, _transport: BaseTransport, _client: object) -> None:
        await self._flow_manager.initialize(self._parts.flow.initial_node())

    async def _on_disconnected(self, _transport: BaseTransport, _client: object) -> None:
        await self._worker.cancel()

    async def _on_caller_heard_again(self, _aggregator: LLMUserAggregator) -> None:
        if self._caller_heard_since is None:
            self._caller_heard_since = time.time()

    async def _on_user_turn_started(
        self, _aggregator: LLMUserAggregator, _strategy: object
    ) -> None:
        next_step = self._parts.flow.when_caller_speaks()
        if next_step is not None:
            await self._flow_manager.set_node_from_config(next_step)

    async def _on_user_turn_stopped(
        self, _aggregator: LLMUserAggregator, _strategy: object, message: UserTurnStoppedMessage
    ) -> None:
        if not message.content:
            return
        parts = self._parts
        parts.feed.caller_said(message.content)
        messages = self._context.get_messages()
        await parts.strategist.advise(parts.conversation(messages), count_caller_turns(messages))

    async def _on_assistant_turn_stopped(
        self, _aggregator: LLMAssistantAggregator, message: AssistantTurnStoppedMessage
    ) -> None:
        if not message.content:
            return
        self._floor.release()
        scripted = self._parts.feed.kenji_said(message.content)
        if scripted == self._kit.script.lines.greeting and not message.interrupted:
            self._parts.session.mark_disclosure_given()

    async def _on_latency(self, _observer: object, breakdown: LatencyBreakdown) -> None:
        started, heard_since = breakdown.user_turn_start_time, self._caller_heard_since
        if started is None or heard_since is None or started < heard_since:
            return  # timed from before the opening, when the caller was muted: not a turn
        opening = self._fast_path.last_opening
        llm_first_token = (
            next((ttfb.duration_secs for ttfb in breakdown.ttfb if "LLM" in ttfb.processor), None)
            if opening == "model"
            else None
        )
        latency = split_turn_latency(
            breakdown.user_turn_secs, llm_first_token, breakdown.total_secs
        )
        if latency is not None:
            self._parts.latency.record(latency, opening)

    def _publish_turn(self, utterance: str, decision: TurnDecision, overlap_ms: float) -> None:
        if decision.verdict is TurnVerdict.BACKCHANNEL:
            self._parts.feed.caller_backchannel(utterance)
        self._parts.io.sink.publish(
            TurnAssessed(
                node=self._parts.session.node,
                utterance=utterance,
                overlap_ms=overlap_ms,
                characters=decision.characters,
                score=decision.score,
                threshold=self._parts.flow.turn_policy().min_interruption_score,
                verdict=decision.verdict,
            )
        )

    async def _end_at_time_limit(self) -> None:
        await asyncio.sleep(self._max_seconds)
        line = self._kit.script.lines.time_up
        self._parts.feed.expect_scripted(line)
        self._parts.session.record("time_limit_reached", {"seconds": self._max_seconds})
        logger.info("call reached its time limit", call_id=self._parts.session.context.call_id)
        await self._worker.queue_frames([TTSSpeakFrame(line.ja), EndFrame()])
