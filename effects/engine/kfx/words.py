"""Word timings: which word is spoken when. Effects use them to hit a beat on a keyword."""
import json
import re
from dataclasses import dataclass


@dataclass
class Word:
    start: float
    end: float
    text: str

    @property
    def clean(self):
        """Lowercase, no punctuation: 'Annoying,' -> 'annoying'."""
        return re.sub(r"[^\w']+", "", self.text.lower())

    def shifted(self, dt):
        return Word(self.start + dt, self.end + dt, self.text)


def load_words(path):
    """Read a transcript with word timings.

    Accepts the formats people actually have:
      - ElevenLabs speech-to-text JSON: {"words": [{"text", "start", "end", "type"}]}
      - Whisper-style JSON: {"segments": [{"words": [{"word", "start", "end"}]}]}
      - a plain list: [{"text" or "word", "start", "end"}]
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "words" in data:
        items = data["words"]
    elif isinstance(data, dict) and "segments" in data:
        items = [w for seg in data["segments"] for w in seg.get("words", [])]
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError(f"{path}: no word timings found (expected 'words' or 'segments')")
    words = []
    for it in items:
        if it.get("type", "word") != "word":
            continue  # ElevenLabs also lists spacing and sound events
        text = (it.get("text") if "text" in it else it.get("word", "")).strip()
        if not text or it.get("start") is None or it.get("end") is None:
            continue
        words.append(Word(float(it["start"]), float(it["end"]), text))
    return words


def window(words, start, end):
    """Words inside [start, end], re-timed so the clip starts at 0."""
    stop = end if end is not None else float("inf")
    return [w.shifted(-start) for w in words if start - 0.05 <= w.start < stop]


def find(words, keywords):
    """All spoken words matching any keyword (case and punctuation ignored), in time order."""
    if isinstance(keywords, str):
        keywords = [keywords]
    wanted = {re.sub(r"[^\w']+", "", k.lower()) for k in keywords if k}
    return [w for w in words if w.clean in wanted]


def word_at(words, t):
    """The word being spoken (or last spoken) at time t, or ''."""
    current = [w for w in words if w.start <= t]
    return current[-1].text.strip(".,!?") if current else ""
