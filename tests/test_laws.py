from myth_grt.laws import NEGLECT_LIMIT, alignment_for, apply_laws, resonance
from myth_grt.world import World


def test_every_breath_is_a_year(world):
    apply_laws(world, "plant a garden")
    apply_laws(world, "plant another")
    assert world.age_in_years == 2


def test_harmony_raises_vitality_and_chaos_lowers_it(world):
    world.vitality = 50
    apply_laws(world, "build a garden of hope")
    assert world.alignment == "Harmonious"
    assert world.vitality == 65

    apply_laws(world, "burn it and destroy everything")
    assert world.alignment == "Chaotic"
    assert world.vitality == 55


def test_vitality_is_clamped(world):
    world.vitality = 98
    apply_laws(world, "heal grow bloom hope peace")
    assert world.vitality == 100
    world.vitality = 3
    apply_laws(world, "war ruin plague curse")
    assert world.vitality == 0


def test_genre_resonance_overrides_alignment():
    drama = World(genre="Drama", elements=["Fire", "Air"])
    apply_laws(drama, "they fall in love")
    assert drama.alignment == "Bittersweet"


def test_resonance_scoring():
    assert resonance("peace and war", "Epic Fantasy") == (0, None)
    assert alignment_for(-1, None) == "Turbulent"
    assert alignment_for(-2, None) == "Chaotic"


def test_maturity_advances_with_age(world):
    reports = [apply_laws(world, "the river sings with light") for _ in range(6)]
    assert world.maturity == "Adolescent"
    assert any(r.matured for r in reports)


def test_lineage_becomes_due_at_adolescence(world):
    reports = [apply_laws(world, "the river sings with light") for _ in range(6)]
    assert not any(r.lineage_due for r in reports[:5])
    assert reports[5].lineage_due


def test_neglect_triggers_emergence(world):
    reports = [apply_laws(world, "nothing in particular") for _ in range(NEGLECT_LIMIT)]
    assert reports[-1].emergent is not None
    assert world.neglect == 0


def test_speaking_to_the_world_resets_neglect(world):
    apply_laws(world, "nothing in particular")
    apply_laws(world, "the water remembers")
    assert world.neglect == 0


def test_withering_is_reported(world):
    world.vitality = 25
    report = apply_laws(world, "war and ruin")
    assert report.withering
    assert world.mood == "fading"
