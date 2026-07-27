"""
Tool: career_arc.

The life-stage career TIMELINE. Walks the mahadasha phases and works out which
career planet's FIELD governs each phase, then detects a future career SHIFT (a
change of governing planet, or an unfavourable->favourable turn).

A person may sit in a lesser field during an unfavourable dasha and shift when a
favourable one begins. The framing depends on life stage:
    forming (youth)  -> the field is still taking shape: predict what the
                        strongest career planet builds and when it establishes.
    established (mid / late) -> the current dasha shows the field they are in
                        now; the next favourable transition flags a possible
                        career shift, with its age window.

Wraps DasaEvaluator.mahadasha_phases. Returns the arc, the shift, the ordered
governing planets, the primary planet, and a human reason.
"""

from core.dasha_evaluator import DasaEvaluator
from utils.constant import PLANET_PROFESSIONS

NAME = "career_arc"

_FORMING_STAGES = {"child", "youth"}


def _governing(phase, ranked):
    """Which career planet's field governs a phase. If the dasha lord is itself a
    career planet, its field leads; otherwise the strongest career planet during
    favourable periods, the second-strongest during unfavourable ones."""
    if phase["lord"] in ranked:
        return phase["lord"], "dasha lord is a career planet"
    if phase["favourable"] or len(ranked) == 1:
        return ranked[0], "strongest career planet (favourable period)"
    return ranked[1], "second career planet (unfavourable period)"


def run(ctx, ranked, life_stage):
    forming = life_stage in _FORMING_STAGES
    phases = DasaEvaluator.mahadasha_phases(ctx)

    if not ranked:
        return {"phases": [], "shift": None, "ordered": [], "primary_planet": None,
                "reason": "no career planets connected"}

    # No dasha timeline: fall back to natal strength only.
    if not phases:
        return {
            "phases": [], "shift": None, "ordered": ranked[:2],
            "primary_planet": ranked[0],
            "reason": f"{ranked[0]} chosen on natal strength (no dasha timeline)",
        }

    past = [p for p in phases if p["tag"] == "PAST"]
    active = [p for p in phases if p["tag"] == "ACTIVE"]
    upcoming = [p for p in phases if p["tag"] == "UPCOMING"]

    if forming:
        window = active[:1] + upcoming[:2]
    else:
        window = past[-1:] + active[:1] + upcoming[:2]
    if not window:
        window = phases[:3]

    arc = []
    for p in window:
        g, why = _governing(p, ranked)
        arc.append({
            "lord": p["lord"], "tag": p["tag"], "favourable": p["favourable"],
            "score": p["score"], "age_start": p.get("age_start"),
            "age_end": p.get("age_end"), "governing_planet": g,
            "governing_reason": why, "field_sample": PLANET_PROFESSIONS.get(g, [])[:3],
        })

    # First transition INTO A FUTURE period = a shift. A shift into the current
    # period already happened and is not a prediction.
    shift = None
    for prev, nxt in zip(arc, arc[1:]):
        if nxt["tag"] != "UPCOMING":
            continue
        field_change = nxt["governing_planet"] != prev["governing_planet"]
        fortune_up = (not prev["favourable"]) and nxt["favourable"]
        if field_change or fortune_up:
            shift = {
                "type": "field_change" if field_change else "fortune_change",
                "from_planet": prev["governing_planet"],
                "to_planet": nxt["governing_planet"],
                "at_age": nxt.get("age_start"),
                "dasa": nxt["lord"],
                "favourable_after": nxt["favourable"],
            }
            break

    if forming:
        primary_planet = ranked[0]
        reason = (
            f"early career: field forms around {primary_planet}"
            + (f", establishing near age {shift['at_age']}" if shift else "")
        )
    else:
        current = active[0] if active else window[0]
        primary_planet, _ = _governing(current, ranked)
        if shift and shift["type"] == "field_change":
            reason = (
                f"currently a {primary_planet} field; possible shift toward "
                f"{shift['to_planet']} around age {shift['at_age']} "
                f"({shift['dasa'].title()} dasha)"
            )
        elif shift and shift["type"] == "fortune_change":
            reason = (
                f"{primary_planet} field strengthens around age "
                f"{shift['at_age']} as the dasha turns favourable"
            )
        else:
            reason = f"established {primary_planet} field, steady through upcoming dashas"

    order_seed = [primary_planet]
    if shift:
        order_seed.append(shift["to_planet"])
    order_seed += [a["governing_planet"] for a in arc] + ranked
    ordered = []
    for g in order_seed:
        if g and g not in ordered:
            ordered.append(g)

    return {
        "phases": arc, "shift": shift, "ordered": ordered,
        "primary_planet": primary_planet, "reason": reason,
    }
