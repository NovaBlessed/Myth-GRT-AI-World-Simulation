"""World state: the data model, genesis options, and save/load."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2

GENRES = ["Comedy", "Drama", "Action", "Mystery", "Horror", "Romance", "Epic Fantasy", "Sci-Fi"]
ELEMENTS = ["Fire", "Water", "Earth", "Air", "Light", "Shadow"]
PHENOMENA = ["Flight", "Telepathy", "Alchemy", "Dreamwalking", "Time Distortion"]

# The world grows up as the Architect keeps breathing life into it.
MATURITY_STAGES = [
    (0, "Newborn"),
    (3, "Infant"),
    (6, "Adolescent"),
    (12, "Mature"),
    (24, "Ancient"),
]

ALIGNMENTS = ["Harmonious", "Neutral", "Bittersweet", "Turbulent", "Chaotic"]


@dataclass
class Lineage:
    """A people that emerges once the world is old enough to hold them."""

    name: str
    purpose: str
    spirit_trait: str
    born_in_year: int


@dataclass
class Chronicle:
    """One permanent entry in the world's history (Law of Irreversibility)."""

    year: int
    breath: str
    narration: str
    alignment: str
    vitality: int
    events: list[str] = field(default_factory=list)


@dataclass
class World:
    """Everything the simulation knows about one world."""

    genre: str
    elements: list[str]
    phenomena: list[str] = field(default_factory=list)
    name: str = "Primordia"
    age_in_years: int = 0
    maturity: str = "Newborn"
    vitality: int = 100
    alignment: str = "Neutral"
    mood: str = "restless"
    neglect: int = 0
    resonance: int = 0
    landmarks: list[str] = field(default_factory=list)
    lineages: list[Lineage] = field(default_factory=list)
    history: list[Chronicle] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.genre not in GENRES:
            raise ValueError(f"Unknown genre {self.genre!r}. Choose one of: {', '.join(GENRES)}")
        if len(self.elements) != 2 or any(e not in ELEMENTS for e in self.elements):
            raise ValueError(f"A world needs exactly two elements from: {', '.join(ELEMENTS)}")
        if len(self.phenomena) > 2 or any(p not in PHENOMENA for p in self.phenomena):
            raise ValueError(f"Choose up to two phenomena from: {', '.join(PHENOMENA)}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "World":
        data = dict(data)
        data["lineages"] = [Lineage(**lin) for lin in data.get("lineages", [])]
        data["history"] = [Chronicle(**entry) for entry in data.get("history", [])]
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


def maturity_for_age(age: int) -> str:
    """Return the maturity stage a world reaches at a given age."""
    stage = MATURITY_STAGES[0][1]
    for threshold, name in MATURITY_STAGES:
        if age >= threshold:
            stage = name
    return stage


def migrate_v1(data: dict[str, Any]) -> dict[str, Any]:
    """Upgrade a save file written by the original 2025 engine."""
    history = [
        {
            "year": int(str(item.get("timestamp", "0")).split()[0] or 0),
            "breath": item.get("breath", ""),
            "narration": "",
            "alignment": data.get("spirit_alignment", "Neutral"),
            "vitality": data.get("world_vitality", 100),
            "events": [],
        }
        for item in data.get("history", [])
    ]
    return {
        "genre": data.get("genre") or "Epic Fantasy",
        "elements": (data.get("elements") or ["Light", "Shadow"])[:2],
        "phenomena": (data.get("phenomena") or [])[:2],
        "age_in_years": data.get("age_in_years", 0),
        "maturity": maturity_for_age(data.get("age_in_years", 0)),
        "vitality": data.get("world_vitality", 100),
        "alignment": data.get("spirit_alignment", "Neutral"),
        "mood": data.get("emotional_temperature", "restless"),
        "lineages": [
            {
                "name": lin.get("name", "The Unnamed"),
                "purpose": lin.get("purpose", ""),
                "spirit_trait": lin.get("spirit_trait", "Neutral"),
                "born_in_year": 0,
            }
            for lin in data.get("lineages", [])
        ],
        "history": history,
    }


def load_world(path: Path) -> World | None:
    """Load a world from disk. Returns None if there is no save yet."""
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version", 1) < SCHEMA_VERSION:
        data = migrate_v1(data)
    return World.from_dict(data)


def save_world(world: World, path: Path) -> None:
    """Save atomically, so a crash mid-write can never corrupt a world."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".world-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(world.to_dict(), handle, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
