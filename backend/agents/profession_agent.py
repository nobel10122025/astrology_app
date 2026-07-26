"""
Profession agent - the first real agent.

Pure declaration: a checklist (10th/2nd/lagna houses + their lords), the
activators that time a career phase (10th & 2nd lords + career karakas), topics,
and age minimums. All logic runs in BaseAgent via the rule engine.

To add another domain: copy this file, change the declarations, register.
"""

from agents.base_agent import BaseAgent
from agents.registry import AgentRegistry
from core.chart_query import ChartQuery
from core.dasha_evaluator import DasaEvaluator
from core.signification import resolve_fields
from utils.constant import PLANET_PROFESSIONS


class ProfessionAgent(BaseAgent):
    name = "profession"
    domain = "profession"
    topics = ["profession", "career", "job", "work", "occupation"]
    min_age = 18
    realistic_age = 22

    CHECKLIST = [
        {"check": "house_strength", "house": 10, "weight": 2},
        {"check": "house_lord_strength", "house": 10, "weight": 2},
        {"check": "house_strength", "house": 2, "weight": 1},
        {"check": "house_lord_strength", "house": 2, "weight": 1},
        {"check": "lagna_strength", "weight": 1},
        {"check": "lagna_lord_strength", "weight": 1},
    ]

    # Career fires in the dasha/antardasha of the 10th & 2nd lords, or of the
    # classic career karakas (Sun=authority, Saturn=work/service, Mercury=skill).
    ACTIVATOR_HOUSES = [10, 2]
    ACTIVATOR_PLANETS = ["sun", "saturn", "mercury"]

    # The career houses whose "connection in any way" determines the field.
    CAREER_HOUSES = [10, 2]

    # Life-stage boundaries (years). Judgment calls - tune against known charts.
    LIFE_STAGE_START_MAX = 30   # below this: career still forming
    LIFE_STAGE_LATE_MIN = 55    # at/above this: late career

    def _life_stage(self, age):
        if age is None or age < self.LIFE_STAGE_START_MAX:
            return "start"
        if age >= self.LIFE_STAGE_LATE_MIN:
            return "late"
        return "mid"

    def _governing_planet(self, phase, ranked):
        """Which career planet's FIELD governs a dasha phase.

        If the dasha lord is itself a career planet, that planet's field leads.
        Otherwise the natal strongest career planet governs during favourable
        periods; during unfavourable periods the second-strongest does (the
        person tends to end up in the lesser field while the dasha is weak)."""
        if phase["lord"] in ranked:
            return phase["lord"], "dasha lord is a career planet"
        if phase["favourable"] or len(ranked) == 1:
            return ranked[0], "strongest career planet (favourable period)"
        return ranked[1], "second career planet (unfavourable period)"

    def refine(self, ctx, result):
        """Life-stage-aware career arc.

        Career-defining planets are those CONNECTED to the career houses (10th,
        2nd) in any way - ranked by strength. But the FIELD is not one static
        answer: it tracks the dasha timeline. A person may sit in a lesser field
        during an unfavourable dasha and shift when a favourable one begins.

        - start of life  -> career is still forming: predict the field the
          strongest career planet builds, timed to the coming favourable dasha.
          (Looking at "the next 2 dashas" to pick a planet is meaningless here.)
        - mid / late     -> read the arc: the current dasha shows the field they
          are likely in now, and a change of governing planet (or an
          unfavourable->favourable turn) ahead flags a possible career SHIFT,
          with its age window.
        """
        q = ChartQuery(ctx)
        connected = q.planets_connected_to_group(self.CAREER_HOUSES)
        ranked = [p for p in connected if p in PLANET_PROFESSIONS]
        ranked.sort(key=lambda p: ctx.scores.get(p, 0), reverse=True)
        if not ranked:
            result.detail["profession_planets"] = []
            result.detail["indicated_professions"] = []
            return result

        # Semantic layer: combine the significations (meaning tags) of the top
        # career-connected planets - their own tags + their sign's + their
        # house's - into ranked SPECIFIC fields (e.g. government + astronomy ->
        # space research / ISRO-NASA). This answers "what field", where the
        # score only answers "how good / when".
        career_planets = list(connected)[:3]
        result.detail["field_profile"] = resolve_fields(career_planets, ctx)

        life_stage = self._life_stage(ctx.current_age)
        phases = DasaEvaluator.mahadasha_phases(ctx)

        # No timeline (no birth date): fall back to natal strength only.
        if not phases:
            ordered = ranked[:2]
            self._attach(result, ordered, connected)
            result.detail["career_arc"] = {"life_stage": life_stage, "phases": []}
            result.detail["career_shift"] = None
            result.detail["profession_selection"] = {
                "chosen": ordered[0],
                "reason": f"{ordered[0]} chosen on natal strength (no dasha timeline)",
            }
            return result

        past = [p for p in phases if p["tag"] == "PAST"]
        active = [p for p in phases if p["tag"] == "ACTIVE"]
        upcoming = [p for p in phases if p["tag"] == "UPCOMING"]

        # Window of relevant phases. The young get a forward-looking window; the
        # established also get the most recent past for "how you got here".
        if life_stage == "start":
            window = active[:1] + upcoming[:2]
        else:
            window = past[-1:] + active[:1] + upcoming[:2]
        if not window:
            window = phases[:3]

        arc = []
        for p in window:
            g, why = self._governing_planet(p, ranked)
            arc.append({
                "lord": p["lord"],
                "tag": p["tag"],
                "favourable": p["favourable"],
                "score": p["score"],
                "age_start": p.get("age_start"),
                "age_end": p.get("age_end"),
                "governing_planet": g,
                "governing_reason": why,
                "field_sample": PLANET_PROFESSIONS.get(g, [])[:3],
            })

        # First meaningful transition INTO A FUTURE period = a career shift
        # (field change) or a fortune turn (unfavourable -> favourable). Only
        # UPCOMING transitions count; a shift into the current period already
        # happened and is not a prediction.
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

        # Primary field: what the person builds (start) or is in now (mid/late).
        if life_stage == "start":
            primary_planet = ranked[0]
            reason = (
                f"early career: field forms around {primary_planet}"
                + (f", establishing near age {shift['at_age']}" if shift else "")
            )
        else:
            current = active[0] if active else window[0]
            primary_planet, _ = self._governing_planet(current, ranked)
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

        # Field list: primary first, then any shift target, then remaining ranked.
        order_seed = [primary_planet]
        if shift:
            order_seed.append(shift["to_planet"])
        order_seed += [a["governing_planet"] for a in arc] + ranked
        ordered = []
        for g in order_seed:
            if g and g not in ordered:
                ordered.append(g)

        self._attach(result, ordered, connected)
        result.detail["career_arc"] = {"life_stage": life_stage, "phases": arc}
        result.detail["career_shift"] = shift
        result.detail["profession_selection"] = {
            "chosen": primary_planet,
            "life_stage": life_stage,
            "reason": reason,
        }
        return result

    @staticmethod
    def _attach(result, ordered, connected):
        """Attach the field list, professions, and connection evidence."""
        professions = []
        for planet in ordered:
            for job in PLANET_PROFESSIONS.get(planet, []):
                if job not in professions:
                    professions.append(job)
        result.detail["profession_planets"] = ordered
        result.detail["indicated_professions"] = professions
        result.detail["career_connections"] = {
            p: connected[p] for p in ordered if p in connected
        }


AgentRegistry.register(ProfessionAgent())
