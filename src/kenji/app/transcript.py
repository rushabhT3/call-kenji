"""The live transcript: Japanese lines as they happen, English subtitles a moment later."""

import asyncio
import itertools

from loguru import logger

from kenji.app.events import Subtitle, TranscriptLine
from kenji.app.ports import Clock, EventSink, Translator
from kenji.app.script import Line
from kenji.domain.text import (
    spoken_characters,
    without_repeated_sentence_ends,
    without_stray_latin_words,
)

TRANSLATION_TIMEOUT_SECS = 15.0


def _key(japanese: str) -> str:
    return spoken_characters(japanese)


class TranscriptFeed:
    def __init__(self, sink: EventSink, translator: Translator, clock: Clock) -> None:
        self._sink = sink
        self._translator = translator
        self._clock = clock
        self._scripted: dict[str, Line] = {}
        self._line_numbers = itertools.count(1)
        self._caller_line_id: str | None = None
        self._translations: set[asyncio.Task[None]] = set()

    def expect_scripted(self, line: Line) -> None:
        self._scripted[_key(line.ja)] = line

    def caller_partial(self, japanese: str) -> None:
        if self._caller_line_id is None:
            self._caller_line_id = self._next_id("caller")
        self._publish(self._caller_line_id, "caller", japanese, is_final=False)

    def caller_said(self, japanese: str) -> None:
        line_id = self._caller_line_id or self._next_id("caller")
        self._caller_line_id = None
        self._publish(line_id, "caller", japanese, is_final=True)
        self._translate_later(line_id, japanese)

    def caller_backchannel(self, japanese: str) -> None:
        line_id = self._caller_line_id or self._next_id("caller")
        self._caller_line_id = None
        self._publish(line_id, "caller", japanese, is_final=True, is_backchannel=True)

    def kenji_said(self, japanese: str) -> Line | None:
        """Publish what Kenji said; the speech service's word timing can repeat a final 。."""
        line_id = self._next_id("kenji")
        scripted = self._scripted.get(_key(japanese))
        if scripted is None:
            spoken = without_stray_latin_words(without_repeated_sentence_ends(japanese))
            self._publish(line_id, "kenji", spoken, is_final=True)
            self._translate_later(line_id, spoken)
        else:
            self._publish(line_id, "kenji", scripted.ja, is_final=True)
            self._sink.publish(Subtitle(line_id=line_id, en=scripted.en))
        return scripted

    async def drain(self) -> None:
        if self._translations:
            await asyncio.gather(*self._translations, return_exceptions=True)

    def _next_id(self, speaker: str) -> str:
        return f"{speaker}-{next(self._line_numbers)}"

    def _publish(
        self,
        line_id: str,
        speaker: str,
        japanese: str,
        *,
        is_final: bool,
        is_backchannel: bool = False,
    ) -> None:
        self._sink.publish(
            TranscriptLine.model_validate(
                {
                    "line_id": line_id,
                    "speaker": speaker,
                    "ja": japanese,
                    "is_final": is_final,
                    "is_backchannel": is_backchannel,
                    "at": self._clock.now(),
                }
            )
        )

    def _translate_later(self, line_id: str, japanese: str) -> None:
        task = asyncio.create_task(self._translate(line_id, japanese))
        self._translations.add(task)
        task.add_done_callback(self._translations.discard)

    async def _translate(self, line_id: str, japanese: str) -> None:
        try:
            english = await asyncio.wait_for(
                self._translator.translate(japanese), TRANSLATION_TIMEOUT_SECS
            )
        except Exception:
            logger.exception("subtitle translation failed", line_id=line_id)
            return
        self._sink.publish(Subtitle(line_id=line_id, en=english))
