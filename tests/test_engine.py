import pytest

from myth_grt.chronicle import to_markdown
from myth_grt.engine import take_turn
from myth_grt.mind import MindError, Narration, OfflineMind


class BrokenMind:
    name = "broken"

    def narrate(self, world, breath, report):
        raise MindError("Claude is rate-limited right now.")


class ScriptedMind:
    name = "scripted"

    def __init__(self, **fields):
        self.fields = fields

    def narrate(self, world, breath, report):
        return Narration(narration="The world answers.", omen="Soon.", source="scripted", **self.fields)


def test_turn_records_history(world):
    result = take_turn(world, "plant a garden of light", OfflineMind())
    assert world.age_in_years == 1
    assert world.history[-1].breath == "plant a garden of light"
    assert result.narration.narration


def test_empty_breath_is_rejected(world):
    with pytest.raises(ValueError):
        take_turn(world, "   ", OfflineMind())


def test_offline_narration_is_deterministic(world):
    from myth_grt.world import World

    twin = World(genre=world.genre, elements=list(world.elements), phenomena=list(world.phenomena))
    a = take_turn(world, "raise a tower of light", OfflineMind())
    b = take_turn(twin, "raise a tower of light", OfflineMind())
    assert a.narration.narration == b.narration.narration


def test_falls_back_when_the_mind_fails(world):
    result = take_turn(world, "build a bridge", BrokenMind())
    assert result.narration.source == "offline"
    assert "rate-limited" in result.note


def test_new_landmark_is_added_once(world):
    mind = ScriptedMind(landmark="The Glass Reach")
    take_turn(world, "build", mind)
    take_turn(world, "build again", mind)
    assert world.landmarks == ["The Glass Reach"]


def test_lineage_is_born_at_adolescence(world):
    for _ in range(5):
        take_turn(world, "the river sings with light", OfflineMind())
    assert world.lineages == []
    result = take_turn(world, "the river sings with light", OfflineMind())
    assert result.new_lineage is not None
    assert world.lineages[0].born_in_year == 6


def test_lineage_still_born_if_narrator_skips_it(world):
    for _ in range(5):
        take_turn(world, "the river sings with light", OfflineMind())
    result = take_turn(world, "the river sings with light", ScriptedMind())
    assert result.new_lineage is not None
    assert result.new_lineage.name


def test_chronicle_export(world):
    take_turn(world, "plant a garden of light", OfflineMind())
    markdown = to_markdown(world)
    assert markdown.startswith("# The Chronicle of Primordia")
    assert "> plant a garden of light" in markdown
