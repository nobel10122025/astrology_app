"""
ProfessionMainAgent - a main agent that plans and triggers tools.

Instead of one fixed routine, this agent is a deterministic PLANNER: it reads the
person's age, decides the life stage, and triggers the age-appropriate tools
(who / how good / when / what field / arc), wiring their outputs together into a
single result. Which tools ran is recorded in detail["tools_run"] for audit.

    age -> plan(stage) -> [tools] -> ProfessionResult -> (merge) -> narrate (LLM)

The tools are the deterministic capabilities in tools/; the only LLM call in the
whole system remains the narrator at the edge. Output shape is unchanged so the
frontend cards keep working.
"""

from agents.base_agent import AgentResult, BaseAgent
from agents.profession_planner import resolve_plan
from agents.registry import AgentRegistry
from core.rule_engine import SpecialFlagInjector
from tools import (
    career_arc,
    career_significators,
    dasha_favourability,
    field_resolver,
    strength,
    timing,
)
from utils.constant import PLANET_PROFESSIONS


class ProfessionMainAgent(BaseAgent):
    name = "profession"
    domain = "profession"
    topics = ["profession", "career", "job", "work", "occupation"]

    CHECKLIST = [
        {"check": "house_strength", "house": 10, "weight": 2},
        {"check": "house_lord_strength", "house": 10, "weight": 2},
        {"check": "house_strength", "house": 2, "weight": 1},
        {"check": "house_lord_strength", "house": 2, "weight": 1},
        {"check": "lagna_strength", "weight": 1},
        {"check": "lagna_lord_strength", "weight": 1},
    ]

    # Career fires in the dasha of the 10th & 2nd lords, or the career karakas.
    ACTIVATOR_HOUSES = [10, 2]
    ACTIVATOR_PLANETS = ["sun", "saturn", "mercury"]

    # The career houses whose "connection in any way" determines the field.
    CAREER_HOUSES = [10, 2]

    def run(self, ctx):
        """Trigger significators, let the planner decide the rest, assemble."""
        ran = []

        # WHO shapes the career (always; its facts also inform planning) -------
        sig = career_significators.run(ctx, tuple(self.CAREER_HOUSES))
        ran.append(career_significators.NAME)
        connected = sig["connected"]
        ranked = sig["ranked"]
        career_planets = sig["career_planets"]

        # PLAN: the LLM decides which further tools to run (deterministic
        # fallback if the LLM is unavailable). It chooses tools, not astrology.
        plan_context = {
            "age": ctx.current_age,
            "has_dasha_timeline": bool(ctx.tagged_periods),
            "num_career_planets": len(ranked),
            "active_dasha": ctx.active_dasha,
        }
        stage, tool_plan, planner_kind, planner_reasoning = resolve_plan(plan_context)
        detail = {
            "life_stage": stage,
            "planner": {
                "kind": planner_kind,
                "tools": tool_plan,
                "reasoning": planner_reasoning,
            },
        }

        # WHAT field (always) -------------------------------------------------
        detail["field_profile"] = field_resolver.run(ctx, career_planets)
        ran.append(field_resolver.NAME)

        # HOW GOOD ------------------------------------------------------------
        score, breakdown = None, []
        if strength.NAME in tool_plan:
            s = strength.run(ctx, self.CHECKLIST)
            score, breakdown = s["score"], s["breakdown"]
            ran.append(strength.NAME)

        # FIELDS OVER TIME + possible shift -----------------------------------
        ordered = ranked[:2]
        primary = ranked[0] if ranked else None
        sel_reason = f"{stage} aptitude from natal significators"
        if career_arc.NAME in tool_plan and ranked:
            arc = career_arc.run(ctx, ranked, stage)
            ran.append(career_arc.NAME)
            ordered = arc["ordered"] or ordered
            primary = arc["primary_planet"] or primary
            sel_reason = arc["reason"]
            detail["career_arc"] = {"life_stage": stage, "phases": arc["phases"]}
            detail["career_shift"] = arc["shift"]

        # DASHA CLIMATE -------------------------------------------------------
        if dasha_favourability.NAME in tool_plan:
            detail["dasha_outlook"] = dasha_favourability.run(ctx)
            ran.append(dasha_favourability.NAME)

        # WHEN ----------------------------------------------------------------
        timing_res = {"timing": "GENERAL", "age_range": None, "dasa_context": None}
        if timing.NAME in tool_plan:
            timing_res = timing.run(ctx, self._resolve_activators(ctx))
            ran.append(timing.NAME)

        tag = timing_res["timing"]
        if stage == "youth" and tag in ("PAST", "GENERAL"):
            tag = "UPCOMING"          # a forming career is forward-looking
        if stage == "child":
            tag = "GENERAL"           # aptitude, not a timed event

        # Assemble the field list from the chosen planets ---------------------
        planets_for_fields = ordered if ordered else ranked[:2]
        professions = []
        for p in planets_for_fields:
            for job in PLANET_PROFESSIONS.get(p, []):
                if job not in professions:
                    professions.append(job)

        detail["profession_planets"] = planets_for_fields
        detail["indicated_professions"] = professions
        detail["career_connections"] = {
            p: connected[p] for p in planets_for_fields if p in connected
        }
        detail["profession_selection"] = {
            "chosen": primary,
            "life_stage": stage,
            "reason": sel_reason,
        }
        detail["tools_run"] = ran

        flags = SpecialFlagInjector.inject(self.domain, ctx)
        summary = (
            f"profession: early aptitude ({stage})"
            if stage == "child"
            else self._summary(score, tag)
        )

        return AgentResult(
            domain=self.domain,
            topics=self.topics,
            score=score,
            summary=summary,
            timing=tag,
            age_range=timing_res["age_range"],
            dasa_context=timing_res["dasa_context"],
            breakdown=breakdown,
            special_flags=flags,
            detail=detail,
            confidence=self._confidence(score, tag),
            skipped=False,
        )


AgentRegistry.register(ProfessionMainAgent())
