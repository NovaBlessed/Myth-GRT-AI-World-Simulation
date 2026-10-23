"""The Sacred Laws: deterministic rules that run on every breath.

The laws decide *what* changes in the world. The Primordial Mind (an LLM) only
decides *how it is told*. Keeping the rules in plain, tested code means the
simulation stays consistent no matter what the narrator writes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .world import World, maturity_for_age

HARMONY_WORDS = {
    "peace", "garden", "create", "build", "bless", "hope", "heal", "grow", "light",
    "song", "plant", "shelter", "kindness", "gift", "dawn", "bloom", "unite", "teach",
}
CHAOS_WORDS = {
    "war", "burn", "curse", "destroy", "break", "fear", "storm", "ruin", "poison",
    "shatter", "flood", "plague", "betray", "rage", "hunger", "conquer", "silence",
}
# Genre-specific resonance: some genres hear certain words differently.
GENRE_RESONANCE = {
    "Drama": {"love": "Bittersweet", "betray": "Turbulent", "farewell": "Bittersweet"},
    "Romance": {"love": "Harmonious", "heartbreak": "Turbulent"},
    "Horror": {"whisper": "Turbulent", "door": "Turbulent"},
    "Comedy": {"cheese": "Harmonious", "banana": "Harmonious"},
}

VITALITY_STEP = 5
NEGLECT_LIMIT = 3          # breaths that ignore the world's nature before something emerges
WITHERING_THRESHOLD = 20


@dataclass
class LawReport:
    """What the laws decided for one breath, handed to the narrator."""

    year: int
    alignment: str
    vitality: int
    vitality_change: int
    maturity: str
    matured: bool = False
    emergent: str | None = None
    lineage_due: bool = False
    withering: bool = False
    events: list[str] = field(default_factory=list)


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z']+", text.lower()))


def resonance(breath: str, genre: str) -> tuple[int, str | None]:
    """Score a breath (+harmony / -chaos) and find any genre-specific override."""
    words = _words(breath)
    score = len(words & HARMONY_WORDS) - len(words & CHAOS_WORDS)
    override = None
    for trigger, alignment in GENRE_RESONANCE.get(genre, {}).items():
        if trigger in words:
            override = alignment
    return score, override


def alignment_for(score: int, override: str | None) -> str:
    if override:
        return override
    if score > 0:
        return "Harmonious"
    if score == 0:
        return "Neutral"
    if score == -1:
        return "Turbulent"
    return "Chaotic"


def mood_for(alignment: str, vitality: int) -> str:
    if vitality <= WITHERING_THRESHOLD:
        return "fading"
    return {
        "Harmonious": "serene" if vitality > 70 else "hopeful",
        "Neutral": "curious",
        "Bittersweet": "wistful",
        "Turbulent": "uneasy",
        "Chaotic": "feverish",
    }.get(alignment, "restless")


def touches_the_world(breath: str, world: World) -> bool:
    """Does the breath speak to anything the world is made of?"""
    words = _words(breath)
    anchors = [*world.elements, *world.phenomena, *world.landmarks, *(l.name for l in world.lineages)]
    return any(_words(anchor) & words for anchor in anchors)


def apply_laws(world: World, breath: str) -> LawReport:
    """Run every Sacred Law on a breath and mutate the world accordingly."""
    previous_maturity = world.maturity

    # Law of Time: every breath is a year.
    world.age_in_years += 1

    # Law of Resonance: words carry weight.
    score, override = resonance(breath, world.genre)
    world.resonance += score
    world.alignment = alignment_for(score, override)
    change = max(-3, min(3, score)) * VITALITY_STEP
    world.vitality = max(0, min(100, world.vitality + change))

    report = LawReport(
        year=world.age_in_years,
        alignment=world.alignment,
        vitality=world.vitality,
        vitality_change=change,
        maturity=world.maturity,
    )

    # Law of Attention: a world ignored will find its own voice.
    if touches_the_world(breath, world):
        world.neglect = 0
    else:
        world.neglect += 1
    if world.neglect >= NEGLECT_LIMIT:
        source = (world.phenomena or world.elements)[world.age_in_years % len(world.phenomena or world.elements)]
        report.emergent = f"A phenomenon of {source} stirs on its own, unbidden"
        report.events.append(report.emergent)
        world.neglect = 0

    # Law of Becoming: worlds grow up.
    world.maturity = maturity_for_age(world.age_in_years)
    report.maturity = world.maturity
    if world.maturity != previous_maturity:
        report.matured = True
        report.events.append(f"{world.name} grows from {previous_maturity} to {world.maturity}")

    # Law of Lineage: once adolescent, the world is ready for its first people.
    if world.maturity in {"Adolescent", "Mature", "Ancient"} and not world.lineages:
        report.lineage_due = True
        report.events.append("The world is ready for its first people")

    # Law of Balance: vitality can run out.
    if world.vitality <= WITHERING_THRESHOLD:
        report.withering = True
        report.events.append("The land is withering")

    world.mood = mood_for(world.alignment, world.vitality)
    return report
