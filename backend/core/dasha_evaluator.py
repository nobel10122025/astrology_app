"""
DasaEvaluator - "is this dasha favourable?" as a shared, deterministic service.

This is NOT a domain agent (it produces no life-domain card). It is a core
evaluator that any agent can consult - the profession agent uses it to decide
whether the strongest career planet will actually deliver, marriage-timing could
use it, and so on.

Favourability is decided by the guarded 12-rule Dasa-Bhukti sub-agent in
`core.dasha_rules`. Each rule states its own applicability condition first ("it
depends") and only applicable rules feed the verdict; the strength anchor still
comes from the existing subathuvam/pabathuvam engine. This module keeps the older
DasaVerdict shape and the timeline helpers (mahadasha_phases / next_periods /
outlook) so the career arc and other callers are unchanged, while delegating the
actual judgement to the rule engine.
"""

from dataclasses import asdict, dataclass, field

from core.age_gate import _age_on, _parse
from core.dasha_rules import (
    FAVOURABLE_THRESHOLD,
    active_period,
    evaluate,
    evaluate_period,
)

__all__ = ["DasaEvaluator", "DasaVerdict", "FAVOURABLE_THRESHOLD"]


@dataclass
class DasaVerdict:
    lord: str
    favourable: bool
    score: float                 # 0-10 favourability
    tag: str = None              # PAST | ACTIVE | UPCOMING (when from a period)
    reasons: list = field(default_factory=list)
    findings: list = field(default_factory=list)   # full per-rule breakdown

    def to_dict(self):
        return asdict(self)


class DasaEvaluator:
    """Evaluate dasha-lord favourability over a ChartContext, via the 12-rule
    sub-agent in core.dasha_rules."""

    @classmethod
    def evaluate_lord(cls, ctx, planet, tag=None, role="maha"):
        """Favourability verdict for a single dasha lord (a planet)."""
        fav = evaluate(ctx, planet, role=role, tag=tag)
        return DasaVerdict(
            lord=fav.lord,
            favourable=fav.favourable,
            score=fav.score,
            tag=fav.tag,
            reasons=fav.reasons or ["no chart data for this planet"],
            findings=fav.findings,
        )

    @classmethod
    def evaluate_period(cls, ctx, maha, bhukti):
        """Judge a maha+bhukti pair (full rules on each + shashtashtaka)."""
        return evaluate_period(ctx, maha, bhukti)

    @classmethod
    def active_period(cls, ctx):
        """Judge the current maha+bhukti period from ctx.active_dasha."""
        return active_period(ctx)

    @classmethod
    def mahadasha_phases(cls, ctx):
        """The full mahadasha timeline as evaluated phases, chronological.

        Each phase carries the lord, its PAST/ACTIVE/UPCOMING tag, its
        favourability verdict, and (when a birth date is known) the age window
        it spans. This is the substrate for a life-stage-aware career arc: a
        person's field can change as the governing dasha changes."""
        phases = []
        for p in sorted(ctx.tagged_periods, key=lambda x: x["start_date"]):
            v = cls.evaluate_lord(ctx, p["lord"], tag=p["tag"])
            entry = {
                "lord": p["lord"],
                "tag": p["tag"],
                "favourable": v.favourable,
                "score": v.score,
                "start_date": p["start_date"],
                "end_date": p["end_date"],
                "reasons": v.reasons,
            }
            if ctx.dob:
                entry["age_start"] = _age_on(ctx.dob, _parse(p["start_date"]))
                entry["age_end"] = _age_on(ctx.dob, _parse(p["end_date"]))
            phases.append(entry)
        return phases

    @classmethod
    def next_periods(cls, ctx, count=2):
        """Evaluate the next `count` mahadasha periods the person is heading into
        (the ACTIVE one plus upcoming ones, chronological). Returns a list of
        DasaVerdict. Empty if no dasha timeline is available."""
        periods = [p for p in ctx.tagged_periods if p["tag"] in ("ACTIVE", "UPCOMING")]
        periods.sort(key=lambda p: p["start_date"])
        verdicts = []
        for p in periods[:count]:
            verdicts.append(cls.evaluate_lord(ctx, p["lord"], tag=p["tag"]))
        return verdicts

    @classmethod
    def outlook(cls, ctx, count=2):
        """Net favourability of the next `count` periods.

        favourable = the average favourability of those periods is at or above
        the threshold. Returns {favourable, avg_score, periods:[verdict...]}.
        When no timeline exists, favourable defaults to True (no reason to
        override the strength-based default choice)."""
        verdicts = cls.next_periods(ctx, count=count)
        if not verdicts:
            return {"favourable": True, "avg_score": None, "periods": [],
                    "note": "no dasha timeline; using strength only"}
        avg = round(sum(v.score for v in verdicts) / len(verdicts), 2)
        return {
            "favourable": avg >= FAVOURABLE_THRESHOLD,
            "avg_score": avg,
            "periods": [v.to_dict() for v in verdicts],
        }
