"""
DasaEvaluator - "is this dasha favourable?" as a shared, deterministic service.

This is NOT a domain agent (it produces no life-domain card). It is a core
evaluator that any agent can consult - the profession agent uses it to decide
whether the strongest career planet will actually deliver, marriage-timing could
use it, and so on.

Favourability of a dasha lord is decided by a small, auditable rule tree over
the immutable ChartContext:

  1. Base strength  - the planet's own subathuva/pabathuvam score (dignity,
                      combustion, aspects... already computed by the engine).
  2. Functional nature - which houses the planet RULES: trikona (5,9) lords are
                      the most benefic, kendra (4,7,10)/lagna lords are helpful,
                      dusthana (6,8,12) lords bring friction.
  3. Placement      - which house the planet SITS in: trikona/kendra good,
                      dusthana difficult.

Each contribution is recorded as a reason so the verdict is explainable and the
narrator can say *why* a period reads as supportive or challenging.
"""

from dataclasses import asdict, dataclass, field

from core.age_gate import _age_on, _parse
from core.chart_query import ChartQuery

KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}
DUSTHANA = {6, 8, 12}

# A favourability score at or above this (0-10) reads as a supportive period.
FAVOURABLE_THRESHOLD = 5.5


@dataclass
class DasaVerdict:
    lord: str
    favourable: bool
    score: float                 # 0-10 favourability
    tag: str = None              # PAST | ACTIVE | UPCOMING (when from a period)
    reasons: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


class DasaEvaluator:
    """Evaluate dasha-lord favourability over a ChartContext."""

    @staticmethod
    def _houses_owned(ctx, planet):
        return [h for h, lord in ctx.house_lords.items() if lord == planet]

    @classmethod
    def evaluate_lord(cls, ctx, planet, tag=None):
        """Favourability verdict for a single dasha lord (a planet)."""
        q = ChartQuery(ctx)
        reasons = []

        base = q.strength(planet)
        if base is None:
            return DasaVerdict(lord=planet, favourable=False, score=0.0, tag=tag,
                               reasons=["no chart data for this planet"])
        reasons.append(f"base strength {base}/10")

        # --- functional nature (what it rules) ---
        func_adj = 0.0
        owned = cls._houses_owned(ctx, planet)
        for h in owned:
            if h in (5, 9):
                func_adj += 1.0
                reasons.append(f"rules trikona {h}th (benefic) +1.0")
            elif h in KENDRA:
                func_adj += 0.5
                reasons.append(f"rules kendra {h}th +0.5")
            elif h in DUSTHANA:
                func_adj -= 1.0
                reasons.append(f"rules dusthana {h}th (friction) -1.0")
        # keep functional swing bounded so one lordship can't dominate
        func_adj = max(-2.0, min(2.0, func_adj))

        # --- placement (where it sits) ---
        place_adj = 0.0
        house = q.house_of(planet)
        if house in TRIKONA:
            place_adj = 1.0
            reasons.append(f"placed in trikona {house}th +1.0")
        elif house in KENDRA:
            place_adj = 0.5
            reasons.append(f"placed in kendra {house}th +0.5")
        elif house in DUSTHANA:
            place_adj = -1.0
            reasons.append(f"placed in dusthana {house}th -1.0")

        score = round(max(0.0, min(10.0, base + func_adj + place_adj)), 2)
        return DasaVerdict(
            lord=planet,
            favourable=score >= FAVOURABLE_THRESHOLD,
            score=score,
            tag=tag,
            reasons=reasons,
        )

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
