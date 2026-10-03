"""The live transcript: Japanese lines as they happen, English subtitles a moment later.

Kenji's line appears as he starts saying it, with its English at once when the line is
scripted. The 「はい、」 he says while the model works, and the holding line, open the line of
the answer that follows rather than standing on their own.
"""

import asyncio
import itertools
from dataclasses import dataclass, field

from loguru import logger

from kenji.app.events import Subtitle, TranscriptLine
from kenji.app.ports import Clock, EventSink, Translator
from kenji.app.script import Line
from kenji.domain.text import (
    spoken_characters,
    without_repeated_sentence_ends,
    without_stray_latin_words,
)

TRANSLATION_TIMEOUT_SECS = 10.0
TRANSLATION_ATTEMPTS = 2


def _key(japanese: str) -> str:
    return spoken_characters(japanese)


def _cleaned(japanese: str) -> str:
    """The speech service's word timing can repeat a final 。, and a model can slip into Latin."""
    return without_stray_latin_words(without_repeated_sentence_ends(japanese))


def _joined(*parts: str) -> str:
    return " ".join(part for part in parts if part)


def _after_finished(sentences: list[str], finished: str) -> list[str]:
    """The sentences of an open line that come after the line Kenji has just finished."""
    said = len(_key(finished))
    spoken = 0
    for index, sentence in enumerate(sentences):
        spoken += len(_key(sentence))
        if spoken >= said:
            return sentences[index + 1 :]
    return []


@dataclass
class _KenjiLine:
    line_id: str
    leads: list[Line] = field(default_factory=list)
    sentences: list[str] = field(default_factory=list)
    english: str | None = None

    @property
    def lead_ja(self) -> str:
        return "".join(lead.ja for lead in self.leads)

    @property
    def lead_en(self) -> str:
        return _joined(*(lead.en for lead in self.leads))

    @property
    def spoken(self) -> str:
        return "".join(self.sentences)


class TranscriptFeed:
    def __init__(self, sink: EventSink, translator: Translator, clock: Clock) -> None:
        self._sink = sink
        self._translator = translator
        self._clock = clock
        self._scripted: dict[str, Line] = {}
        self._leads: dict[str, Line] = {}
        self._line_numbers = itertools.count(1)
        self._caller_line_id: str | None = None
        self._kenji: _KenjiLine | None = None
        self._translations: set[asyncio.Task[None]] = set()

    def expect_scripted(self, line: Line) -> None:
        self._scripted[_key(line.ja)] = line

    def expect_lead(self, line: Line) -> None:
        """A line Kenji says just before an answer, shown as the start of that answer."""
        self._leads[_key(line.ja)] = line

    def caller_partial(self, japanese: str) -> None:
        if self._caller_line_id is None:
            self._caller_line_id = self._next_id("caller")
        self._publish(self._caller_line_id, "caller", japanese, is_final=False)

    def caller_said(self, japanese: str) -> None:
        self._finish_interrupted_line()
        line_id = self._caller_line_id or self._next_id("caller")
        self._caller_line_id = None
        self._publish(line_id, "caller", japanese, is_final=True)
        self._translate_later(line_id, japanese)

    def caller_backchannel(self, japanese: str) -> None:
        line_id = self._caller_line_id or self._next_id("caller")
        self._caller_line_id = None
        self._publish(line_id, "caller", japanese, is_final=True, is_backchannel=True)

    def kenji_speaking(self, sentence: str) -> None:
        """Kenji has started a sentence: his line shows from its first word."""
        line = self._open_kenji_line()
        lead = self._leads.get(_key(sentence))
        if lead is not None and not line.sentences:
            line.leads.append(lead)
        else:
            line.sentences.append(sentence)
        self._publish(line.line_id, "kenji", line.lead_ja + _cleaned(line.spoken), is_final=False)
        english = self._english_so_far(line)
        if english:
            self._subtitle(line, english)

    def kenji_said(self, japanese: str) -> Line | None:
        """Kenji finished a line: publish it as said, and return its script line if it has one."""
        line = self._open_kenji_line()
        self._kenji = None
        scripted = self._finish(line, japanese)
        # The next line's first sentence can start just before this one is reported finished.
        for sentence in _after_finished(line.sentences, japanese):
            self.kenji_speaking(sentence)
        return scripted

    def finish_kenji_line(self) -> None:
        """Close a line Kenji left open, such as a 「はい、」 whose answer never came."""
        line, self._kenji = self._kenji, None
        if line is not None:
            self._finish(line, line.spoken)

    def _finish_interrupted_line(self) -> None:
        """Close a line the caller cut into; a lone 「はい、」 still waits for its answer."""
        if self._kenji is not None and self._kenji.sentences:
            self.finish_kenji_line()

    async def drain(self) -> None:
        self.finish_kenji_line()
        if self._translations:
            await asyncio.gather(*self._translations, return_exceptions=True)

    def _open_kenji_line(self) -> _KenjiLine:
        if self._kenji is None:
            self._kenji = _KenjiLine(self._next_id("kenji"))
        return self._kenji

    def _finish(self, line: _KenjiLine, japanese: str) -> Line | None:
        scripted = self._scripted.get(_key(japanese))
        if scripted is not None:
            self._publish(line.line_id, "kenji", line.lead_ja + scripted.ja, is_final=True)
            self._subtitle(line, _joined(line.lead_en, scripted.en))
            return scripted
        spoken = _cleaned(japanese)
        self._publish(line.line_id, "kenji", line.lead_ja + spoken, is_final=True)
        if spoken:
            self._translate_later(line.line_id, spoken, line.lead_en)
        elif line.lead_en:
            self._subtitle(line, line.lead_en)
        return None

    def _english_so_far(self, line: _KenjiLine) -> str | None:
        """The leads' English, then a scripted line's English once only one line can be meant."""
        if not line.sentences:
            return line.lead_en
        spoken = _key(line.spoken)
        meant = [scripted for key, scripted in self._scripted.items() if key.startswith(spoken)]
        return _joined(line.lead_en, meant[0].en) if len(meant) == 1 else None

    def _subtitle(self, line: _KenjiLine, english: str) -> None:
        if english != line.english:
            line.english = english
            self._sink.publish(Subtitle(line_id=line.line_id, en=english))

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

    def _translate_later(self, line_id: str, japanese: str, lead_en: str = "") -> None:
        task = asyncio.create_task(self._translate(line_id, japanese, lead_en))
        self._translations.add(task)
        task.add_done_callback(self._translations.discard)

    async def _translate(self, line_id: str, japanese: str, lead_en: str) -> None:
        english = await self._translation(line_id, japanese)
        if english is None:
            self._sink.publish(Subtitle(line_id=line_id, en="", is_unavailable=True))
        else:
            self._sink.publish(Subtitle(line_id=line_id, en=_joined(lead_en, english)))

    async def _translation(self, line_id: str, japanese: str) -> str | None:
        """One retry: a slow first request is common, two in a row means the line goes without."""
        for attempt in range(1, TRANSLATION_ATTEMPTS + 1):
            try:
                return await asyncio.wait_for(
                    self._translator.translate(japanese), TRANSLATION_TIMEOUT_SECS
                )
            except Exception:
                logger.exception("subtitle translation failed", line_id=line_id, attempt=attempt)
        return None
