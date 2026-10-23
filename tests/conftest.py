import pytest

from myth_grt.world import World


@pytest.fixture
def world() -> World:
    return World(genre="Epic Fantasy", elements=["Light", "Water"], phenomena=["Dreamwalking"])
