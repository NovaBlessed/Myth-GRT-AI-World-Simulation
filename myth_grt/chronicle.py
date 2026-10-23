"""Export a world's history as a readable Markdown chronicle."""

from __future__ import annotations

from .world import World


def to_markdown(world: World) -> str:
    lines = [
        f"# The Chronicle of {world.name}",
        "",
        f"*A {world.genre} world of {world.elements[0]} and {world.elements[1]}"
        + (f", touched by {' and '.join(world.phenomena)}" if world.phenomena else "")
        + ".*",
        "",
        f"**Age:** {world.age_in_years} years · **Maturity:** {world.maturity} · "
        f"**Vitality:** {world.vitality}/100 · **Spirit:** {world.alignment}",
        "",
    ]
    if world.lineages:
        lines += ["## Peoples", ""]
        lines += [f"- **{l.name}** (year {l.born_in_year}): {l.purpose}" for l in world.lineages]
        lines.append("")
    if world.landmarks:
        lines += ["## Landmarks", "", ", ".join(world.landmarks), ""]
    lines += ["## History", ""]
    for entry in world.history:
        lines.append(f"### Year {entry.year} · {entry.alignment}")
        lines.append("")
        lines.append(f"> {entry.breath}")
        lines.append("")
        if entry.narration:
            lines.append(entry.narration)
            lines.append("")
        for event in entry.events:
            lines.append(f"- {event}")
        if entry.events:
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"
