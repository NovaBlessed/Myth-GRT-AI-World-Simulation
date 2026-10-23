"""ClaudeMind tests use a fake client, so they never call the API."""

import json
from types import SimpleNamespace

import pytest

from myth_grt.laws import apply_laws
from myth_grt.mind import NARRATION_SCHEMA, ClaudeMind, MindError, Narration


def fake_response(payload=None, stop_reason="end_turn", text=None):
    body = text if text is not None else json.dumps(payload)
    return SimpleNamespace(stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=body)])


class FakeClient:
    def __init__(self, response):
        self.calls = []
        self.response = response
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


GOOD = {
    "narration": "Light pools in the river.",
    "omen": "The water remembers.",
    "landmark": "The Shining Ford",
    "lineage_name": "",
    "lineage_purpose": "",
}


def test_request_shape(world):
    client = FakeClient(fake_response(GOOD))
    report = apply_laws(world, "bless the river")
    ClaudeMind(client=client, model="claude-opus-5-5", effort="medium").narrate(world, "bless the river", report)
    call = client.calls[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["fallbacks"] == "default"
    assert call["betas"] == ["server-side-fallback-2026-07-01"]
    assert call["output_config"]["format"]["schema"] == NARRATION_SCHEMA
    assert call["output_config"]["effort"] == "medium"
    assert "temperature" not in call
    brief = json.loads(call["messages"][0]["content"])
    assert brief["breath"] == "bless the river"
    assert brief["world"]["elements"] == ["Light", "Water"]


def test_parses_structured_output(world):
    report = apply_laws(world, "bless the river")
    narration = ClaudeMind(client=FakeClient(fake_response(GOOD))).narrate(world, "bless the river", report)
    assert narration.landmark == "The Shining Ford"
    assert narration.source == "claude"


@pytest.mark.parametrize(
    "response",
    [
        fake_response(GOOD, stop_reason="refusal"),
        fake_response(GOOD, stop_reason="max_tokens"),
        fake_response(text="not json"),
        fake_response({**GOOD, "narration": "   "}),
    ],
)
def test_bad_responses_raise_mind_error(world, response):
    report = apply_laws(world, "anything")
    with pytest.raises(MindError):
        ClaudeMind(client=FakeClient(response)).narrate(world, "anything", report)


def test_payload_is_trimmed():
    narration = Narration.from_payload({**GOOD, "landmark": "x" * 200}, source="claude")
    assert len(narration.landmark) == 48
