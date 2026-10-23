"""One turn of the game: laws first, then narration, then a permanent record."""

from __future__ import annotations

from dataclasses import dataclass

from .laws import LawReport, apply_laws
from .mind import Mind, MindError, Narration, OfflineMind
from .world import Chronicle, Lineage, World

MAX_LANDMARKS = 24


@dataclass
class TurnResult:
    report: LawReport
    narration: Narration
    new_landmark: str = ""
    new_lineage: Lineage | None = None
    note: str = ""  # shown when the narrator had to fall back


def take_turn(world: World, breath: str, mind: Mind, fallback: Mind | None = None) -> TurnResult:
    """Apply the Sacred Laws to a breath, narrate it, and record it forever."""
    breath = " ".join(breath.split())
    if not breath:
        raise ValueError("A breath needs at least one word.")

    report = apply_laws(world, breath)

    note = ""
    try:
        narration = mind.narrate(world, breath, report)
    except MindError as err:
        narration = (fallback or OfflineMind()).narrate(world, breath, report)
        note = f"{err} Using offline narration for this breath."

    result = TurnResult(report=report, narration=narration, note=note)

    landmark = narration.landmark
    if landmark and landmark.lower() not in {l.lower() for l in world.landmarks}:
        world.landmarks = (world.landmarks + [landmark])[-MAX_LANDMARKS:]
        result.new_landmark = landmark
        report.events.append(f"A new landmark appears: {landmark}")

    if report.lineage_due:
        if not narration.lineage_name:
            # The narrator skipped the lineage; the law still has to be honored.
            narration_offline = OfflineMind().narrate(world, breath, report)
            narration.lineage_name = narration_offline.lineage_name
            narration.lineage_purpose = narration_offline.lineage_purpose
        lineage = Lineage(
            name=narration.lineage_name,
            purpose=narration.lineage_purpose,
            spirit_trait=world.alignment,
            born_in_year=world.age_in_years,
        )
        world.lineages.append(lineage)
        result.new_lineage = lineage
        report.events.append(f"A people emerges: {lineage.name}")

    # Law of Irreversibility: every breath becomes permanent history.
    world.history.append(
        Chronicle(
            year=world.age_in_years,
            breath=breath,
            narration=narration.narration,
            alignment=world.alignment,
            vitality=world.vitality,
            events=list(report.events),
        )
    )
    return result
