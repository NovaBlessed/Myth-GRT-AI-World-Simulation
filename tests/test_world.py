import json

import pytest

from myth_grt.world import World, load_world, maturity_for_age, save_world


def test_genesis_is_validated():
    with pytest.raises(ValueError):
        World(genre="Western", elements=["Fire", "Air"])
    with pytest.raises(ValueError):
        World(genre="Drama", elements=["Fire"])
    with pytest.raises(ValueError):
        World(genre="Drama", elements=["Fire", "Air"], phenomena=["Flight", "Alchemy", "Telepathy"])


def test_round_trip(tmp_path, world):
    world.landmarks.append("The Silver Gate")
    path = tmp_path / "w.json"
    save_world(world, path)
    loaded = load_world(path)
    assert loaded == world


def test_missing_save_returns_none(tmp_path):
    assert load_world(tmp_path / "nope.json") is None


def test_save_is_atomic(tmp_path, world):
    path = tmp_path / "w.json"
    save_world(world, path)
    assert [p.name for p in tmp_path.iterdir()] == ["w.json"]


def test_maturity_stages():
    assert maturity_for_age(0) == "Newborn"
    assert maturity_for_age(6) == "Adolescent"
    assert maturity_for_age(30) == "Ancient"


def test_migrates_original_2025_save(tmp_path):
    legacy = {
        "genre": "Horror",
        "elements": ["Shadow", "Water"],
        "phenomena": ["Telepathy"],
        "age_in_years": 7,
        "spirit_alignment": "Chaotic",
        "world_vitality": 40,
        "emotional_temperature": "restless",
        "lineages": [{"name": "The Hollow", "purpose": "watchers"}],
        "history": [{"timestamp": "1 Years", "breath": "open the door"}],
    }
    path = tmp_path / "world_state.json"
    path.write_text(json.dumps(legacy))
    world = load_world(path)
    assert world.genre == "Horror"
    assert world.maturity == "Adolescent"
    assert world.vitality == 40
    assert world.lineages[0].name == "The Hollow"
    assert world.history[0].breath == "open the door"
