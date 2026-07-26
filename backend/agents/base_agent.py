"""
Base agent contract.

An agent DECLARES a checklist, its activator planets/houses, its topics, and
its age minimums. All the actual work - scoring, timing, flag injection - lives
in BaseAgent.run() via the rule engine and age gate. Concrete agents add no
computation; they set class attributes and register themselves.
"""

from abc import ABC
from dataclasses import asdict, dataclass, field

from core.age_gate import TimingResolver
from core.rule_engine import (
    AgeEligibilityGate,
    ChecklistResolver,
    SpecialFlagInjector,
)


@dataclass
class AgentResult:
    domain: str
    topics: list = field(default_factory=list)
    score: float = None          # 0-10 checklist strength
    summary: str = ""            # machine summary (NOT the narrative)
    timing: str = "GENERAL"      # PAST | ACTIVE | UPCOMING | GENERAL
    age_range: str = None        # e.g. "age 32-36"
    dasa_context: str = None     # e.g. "Saturn Mahadasa / Venus Antardasa"
    breakdown: list = field(default_factory=list)
    special_flags: list = field(default_factory=list)
    detail: dict = field(default_factory=dict)
    confidence: float = 0.0
    skipped: bool = False
    skip_reason: str = None

    def to_dict(self):
        return asdict(self)


class BaseAgent(ABC):
    # --- declared by subclasses ---
    name = ""
    domain = ""
    topics = []
    min_age = 0
    realistic_age = 0
    CHECKLIST = []
    ACTIVATOR_HOUSES = []   # houses whose lords time this domain
    ACTIVATOR_PLANETS = []  # significator planets that time this domain

    def _resolve_activators(self, ctx):
        activators = {p.lower() for p in self.ACTIVATOR_PLANETS}
        for h in self.ACTIVATOR_HOUSES:
            lord = ctx.house_lords.get(h)
            if lord:
                activators.add(lord)
        return activators

    def run(self, ctx):
        status = AgeEligibilityGate.check(ctx.current_age, self.min_age, self.realistic_age)
        if status == "skip":
            return AgentResult(
                domain=self.domain,
                topics=self.topics,
                skipped=True,
                skip_reason=f"Below minimum age ({self.min_age}) for {self.domain}",
            )

        resolved = ChecklistResolver.resolve(self.CHECKLIST, ctx)
        activators = self._resolve_activators(ctx)
        timing = TimingResolver.resolve(activators, ctx.dashas, ctx.dob, ctx.today)
        tag = timing["timing"]

        # Not yet at a realistic age -> force forward-looking framing.
        if status == "future" and tag in ("PAST", "GENERAL"):
            tag = "UPCOMING"

        flags = SpecialFlagInjector.inject(self.domain, ctx)
        score = resolved["score"]

        result = AgentResult(
            domain=self.domain,
            topics=self.topics,
            score=score,
            summary=self._summary(score, tag),
            timing=tag,
            age_range=timing["age_range"],
            dasa_context=timing["dasa_context"],
            breakdown=resolved["breakdown"],
            special_flags=flags,
            detail={
                "checklist": resolved["breakdown"],
                "activators": sorted(activators),
            },
            confidence=self._confidence(score, tag),
        )
        # Escape hatch: agents may enrich the result with domain-specific detail
        # (e.g. profession -> which fields). Default is a no-op, so agents that
        # need nothing extra stay pure declarations.
        return self.refine(ctx, result)

    def refine(self, ctx, result):
        """Optional domain-specific enrichment hook. Override to add detail
        without recomputing scores/timing. Must return the (possibly mutated)
        result."""
        return result

    @staticmethod
    def _confidence(score, tag):
        if score is None:
            return 0.3
        base = 0.4 + (score / 10.0) * 0.4
        if tag in ("ACTIVE", "UPCOMING"):
            base += 0.1
        return round(min(0.95, base), 2)

    def _summary(self, score, tag):
        if score is None:
            return f"{self.domain}: insufficient data"
        return f"{self.domain}: strength {score}/10 ({tag})"
