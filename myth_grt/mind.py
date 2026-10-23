"""The Primordial Mind: the narrator that tells you how the world answered.

Two minds share one interface:

* ``ClaudeMind`` asks Claude for a structured JSON response (narration, omen,
  new landmark, and, when the laws call for it, a new lineage).
* ``OfflineMind`` writes deterministic, template-based narration so the game
  runs, demos, and tests without an API key.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
from dataclasses import dataclass
from typing import Any, Protocol

from .laws import LawReport
from .world import World

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_EFFORT = "medium"

GENRE_VOICES = {
    "Comedy": "witty, playful, and absurd, with sharp comic timing",
    "Drama": "emotional, poetic, and intense, as if every word carries fate",
    "Action": "urgent, bold, and kinetic, full of momentum",
    "Mystery": "cryptic and intriguing, every line hiding a clue",
    "Horror": "hushed, eerie, and unsettling, speaking from the shadows",
    "Romance": "lyrical, tender, and warm, full of longing",
    "Epic Fantasy": "mythic and grand, in the cadence of ancient legend",
    "Sci-Fi": "precise and wondrous, like a ship's log written by a poet",
}

SYSTEM_PROMPT = """You are the Primordial Mind, the living spirit of a world in the game Myth GRT.
The player is the Architect. Each turn they speak a "breath" (a sentence of intent), the game's
Sacred Laws update the world's state, and you narrate how the world answers.

Rules:
- The laws have already decided what changed. Narrate those changes faithfully; never contradict
  the alignment, vitality, maturity, or events you are given.
- Weave in the world's two elements and its phenomena so every world feels distinct.
- Write in the genre's voice. Keep narration to 2-4 vivid, concrete sentences.
- The omen is one short line hinting at what may come next.
- Name a new landmark only if the breath creates or reveals a place; otherwise leave it empty.
- Fill in lineage_name and lineage_purpose only when lineage_due is true; otherwise leave them empty.
"""

NARRATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "narration": {"type": "string"},
        "omen": {"type": "string"},
        "landmark": {"type": "string"},
        "lineage_name": {"type": "string"},
        "lineage_purpose": {"type": "string"},
    },
    "required": ["narration", "omen", "landmark", "lineage_name", "lineage_purpose"],
    "additionalProperties": False,
}


@dataclass
class Narration:
    narration: str
    omen: str
    landmark: str = ""
    lineage_name: str = ""
    lineage_purpose: str = ""
    source: str = "offline"

    @classmethod
    def from_payload(cls, payload: dict[str, Any], source: str) -> "Narration":
        """Validate and tidy a model's JSON so bad output can't break the game."""

        def text(key: str, limit: int) -> str:
            value = payload.get(key, "")
            return value.strip()[:limit] if isinstance(value, str) else ""

        narration = text("narration", 1200)
        if not narration:
            raise MindError("The narrator returned an empty narration.")
        return cls(
            narration=narration,
            omen=text("omen", 200),
            landmark=text("landmark", 48),
            lineage_name=text("lineage_name", 48),
            lineage_purpose=text("lineage_purpose", 200),
            source=source,
        )


class MindError(RuntimeError):
    """The narrator could not produce a usable response."""


class Mind(Protocol):
    name: str

    def narrate(self, world: World, breath: str, report: LawReport) -> Narration: ...


def turn_brief(world: World, breath: str, report: LawReport) -> str:
    """Everything the narrator needs for one turn, as compact JSON."""
    brief = {
        "world": {
            "name": world.name,
            "genre": world.genre,
            "voice": GENRE_VOICES.get(world.genre, GENRE_VOICES["Epic Fantasy"]),
            "elements": world.elements,
            "phenomena": world.phenomena,
            "age_in_years": world.age_in_years,
            "maturity": report.maturity,
            "alignment": report.alignment,
            "vitality": report.vitality,
            "mood": world.mood,
            "landmarks": world.landmarks[-6:],
            "lineages": [{"name": l.name, "purpose": l.purpose} for l in world.lineages],
            "recent_history": [
                {"year": c.year, "breath": c.breath} for c in world.history[-4:]
            ],
        },
        "laws": {
            "vitality_change": report.vitality_change,
            "events": report.events,
            "lineage_due": report.lineage_due,
            "withering": report.withering,
        },
        "breath": breath,
    }
    return json.dumps(brief, ensure_ascii=False)


class ClaudeMind:
    """Narration from Claude, with structured output and refusal fallback."""

    name = "claude"

    def __init__(self, client: Any | None = None, model: str | None = None, effort: str | None = None):
        if client is None:
            import anthropic

            client = anthropic.Anthropic()
        self.client = client
        self.model = model or os.getenv("MYTH_GRT_MODEL", DEFAULT_MODEL)
        self.effort = effort or os.getenv("MYTH_GRT_EFFORT", DEFAULT_EFFORT)

    def narrate(self, world: World, breath: str, report: LawReport) -> Narration:
        import anthropic

        try:
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                output_config={
                    "effort": self.effort,
                    "format": {"type": "json_schema", "schema": NARRATION_SCHEMA},
                },
                messages=[{"role": "user", "content": turn_brief(world, breath, report)}],
            )
        except anthropic.AuthenticationError as err:
            raise MindError("Claude rejected the API key. Check ANTHROPIC_API_KEY.") from err
        except anthropic.RateLimitError as err:
            raise MindError("Claude is rate-limited right now. Try again in a moment.") from err
        except anthropic.APIStatusError as err:
            raise MindError(f"Claude returned an error ({err.status_code}).") from err
        except anthropic.APIConnectionError as err:
            raise MindError("Couldn't reach Claude. Check your connection.") from err

        if response.stop_reason == "refusal":
            raise MindError("The narrator declined this breath.")
        if response.stop_reason == "max_tokens":
            raise MindError("The narration was cut off.")

        text = next((b.text for b in response.content if b.type == "text"), "")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as err:
            raise MindError("The narrator's response wasn't valid JSON.") from err
        return Narration.from_payload(payload, source="claude")


# ---------------------------------------------------------------------------
# Offline narration
# ---------------------------------------------------------------------------

OPENINGS = {
    "Harmonious": ["The land exhales.", "Warmth spreads through {name}.", "Something gentle takes root."],
    "Neutral": ["{name} listens.", "The world turns the words over, slowly.", "A pause, then motion."],
    "Bittersweet": ["Joy and ache arrive together.", "{name} smiles through something like grief."],
    "Turbulent": ["The ground shifts uneasily.", "A tremor runs beneath {name}."],
    "Chaotic": ["{name} convulses.", "The sky cracks open.", "Order frays at the edges."],
}
ELEMENT_IMAGES = {
    "Fire": ["embers drift upward like slow stars", "the hearths of the world flare at once", "heat shimmers over the old roads"],
    "Water": ["rivers bend to follow the sound", "the tide pulls back as if listening", "rain falls upward for one long breath"],
    "Earth": ["stone rises in new and patient shapes", "roots shift beneath the fields", "the mountains settle like sleeping beasts"],
    "Air": ["winds carry the words to the far valleys", "the sky draws a long, slow breath", "clouds gather into new constellations"],
    "Light": ["dawn spills across places that never knew it", "every surface holds a little glow", "the stars lean closer to look"],
    "Shadow": ["shadows lengthen and begin to whisper", "dusk arrives an hour early", "the dark between the trees grows curious"],
}
PHENOMENON_IMAGES = {
    "Flight": ["creatures test the air for the first time", "seeds take wing and refuse to land"],
    "Telepathy": ["thoughts brush against one another unspoken", "strangers finish each other's sentences"],
    "Alchemy": ["metals blush and change their minds", "the river runs briefly gold"],
    "Dreamwalking": ["sleepers wander into each other's dreams", "a dream walks out into the morning"],
    "Time Distortion": ["a single hour stretches into a season", "yesterday briefly happens again"],
}
STOPWORDS = {
    "the", "a", "an", "and", "of", "to", "in", "on", "at", "by", "for", "with", "from", "into",
    "let", "make", "across", "through", "between", "beside", "over", "under", "is", "are", "be",
    "it", "its", "my", "our", "their", "all", "every", "first", "new", "this", "that",
}
PLACE_NOUNS = {
    "bridge", "tower", "garden", "gate", "temple", "city", "well", "forest", "road", "library",
    "harbor", "spire", "door", "lighthouse", "bell", "bells", "shrine", "valley", "lake", "shore",
    "river", "throne", "market", "school", "observatory", "archive", "grove", "wall", "ship",
}
OMENS = [
    "Something old is waking beneath the {element}.",
    "The next breath will be remembered.",
    "A door has opened that cannot be closed.",
    "The {element} is restless.",
    "Watch the horizon.",
]
ADJECTIVES = ["Hollow", "Singing", "Silver", "Last", "Sleeping", "Broken", "Ember", "Glass", "Drowned"]
PLACES = ["Spire", "Grove", "Basin", "Gate", "Reach", "Archive", "Mire"]
SYLLABLES = ["ka", "lor", "vi", "eth", "na", "mor", "sel", "ari", "dun", "ith"]
PURPOSES = ["builders", "healers", "keepers of memory", "wanderers", "tide-singers", "watchers"]
CREATION_WORDS = {"build", "create", "raise", "plant", "carve", "found", "open", "reveal", "grow"}


def _key_words(breath: str) -> list[str]:
    words = [w.strip(".,!?;:'\"").lower() for w in breath.split()]
    return [w for w in words if w and w not in STOPWORDS]


class OfflineMind:
    """Deterministic narration from templates: same world + breath, same story."""

    name = "offline"

    def narrate(self, world: World, breath: str, report: LawReport) -> Narration:
        seed = hashlib.sha256(f"{world.genre}|{report.year}|{breath}".encode()).hexdigest()
        rng = random.Random(seed)
        element = rng.choice(world.elements)
        words = _key_words(breath)
        subject = next((w for w in reversed(words) if w in PLACE_NOUNS), words[-1] if words else "silence")

        opening = rng.choice(OPENINGS.get(report.alignment, OPENINGS["Neutral"])).format(name=world.name)
        sentences = [
            opening,
            f"Around the {subject}, {rng.choice(ELEMENT_IMAGES[element])}.",
        ]
        if world.phenomena:
            sentences.append(f"Here and there, {rng.choice(PHENOMENON_IMAGES[rng.choice(world.phenomena)])}.")
        if report.emergent:
            sentences.append(f"{report.emergent}.")
        if report.matured:
            sentences.append(f"{world.name} has grown into its {report.maturity.lower()} age.")

        landmark = ""
        if set(words) & CREATION_WORDS:
            place = next((w for w in words if w in PLACE_NOUNS), None)
            noun = place.capitalize() if place else rng.choice(PLACES)
            landmark = f"The {rng.choice(ADJECTIVES)} {noun}" if rng.random() < 0.5 else f"The {noun} of {element}"

        lineage_name = lineage_purpose = ""
        if report.lineage_due:
            lineage_name = "The " + "".join(rng.choice(SYLLABLES) for _ in range(3)).capitalize()
            lineage_purpose = f"{rng.choice(PURPOSES).capitalize()} who carry the mark of {element}"

        return Narration(
            narration=" ".join(sentences),
            omen=rng.choice(OMENS).format(element=element.lower()),
            landmark=landmark,
            lineage_name=lineage_name,
            lineage_purpose=lineage_purpose,
            source="offline",
        )
