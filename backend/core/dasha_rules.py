"""
Dasa-Bhukti favourability rules - the sub-agent's brain.

The user's rule set for judging whether a Dasa (and Bhukti) period is favourable
is NOT a flat checklist. Its defining property is that *each rule only applies in
certain situations* - "it totally depends". Rahu/Ketu rule no house, so the
functional-nature rule cannot apply to them; a yoga rule only applies when that
yoga is actually present; the shashtashtaka rule only applies when we are judging
a maha+bhukti PAIR; and so on.

So every rule here is a GUARDED function. It first answers `applies` (its
applicability condition), and only applicable rules contribute to the verdict.
Each returns a RuleOutcome carrying the applicability, a signed score delta, a
short verdict label, and a human reason - so the whole judgement is auditable and
the narrator can explain *which* rules fired and why.

The 12 rules (as given by the user):
  R1  Lagna + Lagna-lord strength (chart baseline tone)
  R2  Dasa lord stronger than the Lagna lord
  R3  Which house the Dasa lord rules + its significations  (informational)
  R4  Where the Dasa lord is placed - Kendra / Kona / Dusthana
  R5  Positional + Dig Bala (classic) + Drishti Bala (aspect nature)
  R6  Placement in the bhava - beginning / middle / end of sign
  R7  Natural benefic/malefic + functional (Lagna) benefic/malefic
  R8  Planetary combinations (yogas) - Raja/Dhana/Vipareeta/Neecha-Bhanga + assoc
  R9  Relationship with conjoined planets (friend / enemy)
  R10 The age / life-stage the period grants  (informational context)
  R11 Shashtashtaka: (a) maha<->bhukti 6-8 pairing, (b) 6/8-from-lord affliction
  R12 Dispositor (lord of the sign the Dasa lord sits in) exalted / debilitated

Subathuvam/pabathuvam strength comes from the existing scoring engine (via
ChartQuery.strength), exactly as the user asked ("for subathuvam and papathuvam
we can use the current scoring logic").
"""

from dataclasses import asdict, dataclass, field

from core.chart_query import ChartQuery
from utils.constant import (
    PLANET_DEBILITATION,
    PLANET_EXALTATION,
    PLANET_OWN_HOUSES,
    PLANET_RELATIONSHIPS,
    PLANETS,
)

# A favourability score at or above this (0-10) reads as a supportive period.
FAVOURABLE_THRESHOLD = 5.5

KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}
DUSTHANA = {6, 8, 12}
DHANA_HOUSES = {2, 5, 9, 11}

NATURAL_BENEFICS = {"jupiter", "venus", "mercury", "moon"}
NATURAL_MALEFICS = {"sun", "mars", "saturn", "rahu", "ketu"}

# Classic Dig Bala - the house where each planet has full directional strength,
# and (implicitly) the opposite house where it is weakest.
DIG_BALA_STRONG_HOUSE = {
    "sun": 10, "mars": 10,      # south / meridian - action, status
    "jupiter": 1, "mercury": 1,  # east / ascendant - wisdom, intellect
    "moon": 4, "venus": 4,       # north / nadir - comfort, relationships
    "saturn": 7,                 # west / descendant - endings, labour
}

# Sign -> its ruling planet (dispositor lookup), from own-house ownership.
RASI_LORD = {}
for _p, _signs in PLANET_OWN_HOUSES.items():
    for _s in _signs:
        RASI_LORD[_s] = _p

HOUSE_SIGNIFICATIONS = {
    1: "self, health, personality",
    2: "wealth, family, speech",
    3: "courage, siblings, effort",
    4: "home, mother, comfort, vehicles",
    5: "children, intellect, romance",
    6: "enemies, disease, service, debts",
    7: "marriage, partnership, business",
    8: "longevity, obstacles, inheritance, transformation",
    9: "fortune, dharma, father, higher learning",
    10: "career, status, authority",
    11: "gains, income, elder siblings, friends",
    12: "loss, expense, foreign, moksha",
}

# Life-stage bands (rule 10) - what period of life the dasha grants results in.
LIFE_STAGE_BANDS = [
    (0, 10, "kid"),
    (10, 20, "adolescent"),
    (20, 45, "adult"),
    (45, 65, "older adult"),
    (65, 200, "elderly"),
]


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def life_stage_for_age(age):
    if age is None:
        return None
    for lo, hi, name in LIFE_STAGE_BANDS:
        if lo <= age < hi:
            return name
    return "elderly"


@dataclass
class RuleOutcome:
    rule: str                 # rule id, e.g. "R2_stronger_than_lagna_lord"
    title: str                # human title
    applies: bool             # its applicability guard - the "it depends"
    delta: float = 0.0        # signed favourability contribution (0 if n/a/info)
    verdict: str = "n/a"      # favourable | unfavourable | neutral | info | n/a
    reason: str = ""          # human explanation
    info: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


@dataclass
class DasaFavourability:
    lord: str
    favourable: bool
    score: float                 # 0-10 favourability
    role: str = "maha"           # maha | bhukti
    tag: str = None              # PAST | ACTIVE | UPCOMING (when from a period)
    anchor: float = 0.0          # the strength anchor before rule deltas
    reasons: list = field(default_factory=list)   # applied-rule reasons (strings)
    findings: list = field(default_factory=list)  # full RuleOutcome dicts

    def to_dict(self):
        return asdict(self)


class _RuleCtx:
    """Precomputed facts about one dasha lord - the substrate the rules read.
    Kept read-only; holds no verdict, just chart structure for this lord."""

    def __init__(self, ctx, lord, role="maha", pair_lord=None):
        self.ctx = ctx
        self.q = ChartQuery(ctx)
        self.lord = lord
        self.role = role
        self.pair_lord = pair_lord

        self.house = ctx.planet_houses.get(lord)
        cd = ctx.chart.get(lord) or {}
        self.rasi = cd.get("rasi")
        deg = cd.get("degree")
        self.deg_in_sign = (deg % 30) if deg is not None else None

        self.houses_owned = [h for h, l in ctx.house_lords.items() if l == lord]
        self.strength = self.q.strength(lord)          # 0-10 or None
        self.lagna_lord = ctx.house_lords.get(1)
        self.dispositor = RASI_LORD.get(self.rasi)

        # who touches this lord
        self.conjunct = [
            p for p in PLANETS
            if p != lord and ctx.planet_houses.get(p) == self.house and self.house
        ]
        self.aspecting = [
            p for p in PLANETS
            if p != lord and p in ctx.planet_houses and self.q.aspects_planet(p, lord)
        ]

    def connected(self, other):
        """Is `self.lord` connected to planet `other` (conjunction / mutual
        aspect / sign exchange)? The generic yoga-forming relation."""
        if other == self.lord or other not in self.ctx.planet_houses:
            return False
        oh = self.ctx.planet_houses.get(other)
        if oh == self.house:
            return True
        if self.q.aspects_planet(self.lord, other) or self.q.aspects_planet(other, self.lord):
            return True
        # mutual sign exchange (parivartana)
        my_rasi, their_rasi = self.rasi, (self.ctx.chart.get(other) or {}).get("rasi")
        if my_rasi and their_rasi:
            if their_rasi in PLANET_OWN_HOUSES.get(self.lord, []) and \
               my_rasi in PLANET_OWN_HOUSES.get(other, []):
                return True
        return False

    def owns_lord_of(self, houses):
        """Planets that own any of `houses` and are connected to this lord."""
        lords = {self.ctx.house_lords.get(h) for h in houses} - {None}
        return [p for p in lords if p != self.lord and self.connected(p)]


# --------------------------------------------------------------------------
# The 12 guarded rules. Each: (rc) -> RuleOutcome. `applies=False` means the
# rule's situation does not hold for this lord, so it contributes nothing.
# --------------------------------------------------------------------------

def r1_lagna_baseline(rc):
    lagna_h = rc.q.strength(1)
    lagna_l = rc.q.strength(rc.lagna_lord) if rc.lagna_lord else None
    parts = [v for v in (lagna_h, lagna_l) if v is not None]
    if not parts:
        return RuleOutcome("R1_lagna_baseline", "Lagna & Lagna-lord strength",
                           applies=False, reason="no lagna strength available")
    avg = sum(parts) / len(parts)
    delta = round((avg - 5.0) * 0.10, 3)          # +-0.5 tone
    v = "favourable" if delta > 0.05 else "unfavourable" if delta < -0.05 else "neutral"
    return RuleOutcome(
        "R1_lagna_baseline", "Lagna & Lagna-lord strength", applies=True,
        delta=delta, verdict=v,
        reason=f"lagna/lagna-lord strength {avg:.1f}/10 sets a {v} baseline",
        info={"lagna_house_strength": lagna_h, "lagna_lord_strength": lagna_l},
    )


def r2_stronger_than_lagna_lord(rc):
    if not rc.lagna_lord or rc.lord == rc.lagna_lord:
        return RuleOutcome("R2_stronger_than_lagna_lord", "Stronger than Lagna lord",
                           applies=False,
                           reason="dasa lord is the lagna lord (comparison n/a)")
    ll = rc.q.strength(rc.lagna_lord)
    if rc.strength is None or ll is None:
        return RuleOutcome("R2_stronger_than_lagna_lord", "Stronger than Lagna lord",
                           applies=False, reason="strength unavailable")
    if rc.strength > ll + 0.5:
        return RuleOutcome("R2_stronger_than_lagna_lord", "Stronger than Lagna lord",
                           applies=True, delta=0.7, verdict="favourable",
                           reason=f"dasa lord ({rc.strength}) outshines lagna lord "
                                  f"({ll}) - delivers its own results")
    if rc.strength < ll - 0.5:
        return RuleOutcome("R2_stronger_than_lagna_lord", "Stronger than Lagna lord",
                           applies=True, delta=-0.5, verdict="unfavourable",
                           reason=f"dasa lord ({rc.strength}) weaker than lagna lord "
                                  f"({ll}) - results muted")
    return RuleOutcome("R2_stronger_than_lagna_lord", "Stronger than Lagna lord",
                       applies=True, delta=0.0, verdict="neutral",
                       reason=f"dasa lord ({rc.strength}) ~ lagna lord ({ll})")


def r3_houses_ruled(rc):
    if not rc.houses_owned:
        return RuleOutcome("R3_houses_ruled", "Houses ruled & significations",
                           applies=False,
                           reason=f"{rc.lord} owns no house (node) - rule n/a")
    sig = {h: HOUSE_SIGNIFICATIONS.get(h, "") for h in rc.houses_owned}
    txt = "; ".join(f"{h}th ({s})" for h, s in sig.items())
    return RuleOutcome(
        "R3_houses_ruled", "Houses ruled & significations", applies=True,
        delta=0.0, verdict="info",
        reason=f"rules {txt} - its period colours these areas",
        info={"houses_owned": rc.houses_owned, "significations": sig},
    )


def r4_placement(rc):
    h = rc.house
    if not h:
        return RuleOutcome("R4_placement", "Kendra / Kona / Dusthana placement",
                           applies=False, reason="house placement unknown")
    if h in DUSTHANA:
        return RuleOutcome("R4_placement", "Kendra / Kona / Dusthana placement",
                           applies=True, delta=-0.5, verdict="unfavourable",
                           reason=f"placed in dusthana {h}th - friction")
    if h in TRIKONA:
        return RuleOutcome("R4_placement", "Kendra / Kona / Dusthana placement",
                           applies=True, delta=0.2, verdict="favourable",
                           reason=f"placed in trikona {h}th - supportive")
    if h in KENDRA:
        return RuleOutcome("R4_placement", "Kendra / Kona / Dusthana placement",
                           applies=True, delta=0.1, verdict="favourable",
                           reason=f"placed in kendra {h}th - stable")
    return RuleOutcome("R4_placement", "Kendra / Kona / Dusthana placement",
                       applies=True, delta=0.0, verdict="neutral",
                       reason=f"placed in {h}th - neutral house")


def r5_bala(rc):
    """Positional (anchored in strength) + Dig Bala (classic) + Drishti Bala
    (aspects onto the lord weighted by the aspecting planet's nature)."""
    if rc.lord in ("rahu", "ketu"):
        return RuleOutcome("R5_bala", "Dig Bala & Drishti Bala", applies=False,
                           reason="nodes have no dig bala")
    if not rc.house:
        return RuleOutcome("R5_bala", "Dig Bala & Drishti Bala", applies=False,
                           reason="house placement unknown")
    parts, delta = [], 0.0
    strong = DIG_BALA_STRONG_HOUSE.get(rc.lord)
    if strong:
        weak = ((strong - 1 + 6) % 12) + 1
        if rc.house == strong:
            delta += 0.4
            parts.append(f"full Dig Bala in {strong}th (+0.4)")
        elif rc.house == weak:
            delta -= 0.4
            parts.append(f"no Dig Bala in {weak}th (-0.4)")

    # Drishti Bala: benefic aspects lift, malefic aspects afflict. Nature is both
    # natural AND functional (a functional malefic aspect still afflicts).
    ben = mal = 0
    for p in rc.aspecting:
        nat_ben = p in NATURAL_BENEFICS
        func = _functional_nature(rc.ctx, p)
        if nat_ben or func == "benefic":
            ben += 1
        if (p in NATURAL_MALEFICS) or func == "malefic":
            mal += 1
    net = ben - mal
    if rc.aspecting:
        d = _clamp(net * 0.2, -0.6, 0.6)
        delta += d
        parts.append(f"drishti bala {net:+d} (benefic {ben}/malefic {mal}) {d:+.2f}")

    if not parts:
        return RuleOutcome("R5_bala", "Dig Bala & Drishti Bala", applies=True,
                           delta=0.0, verdict="neutral",
                           reason="no directional or aspectual swing")
    delta = round(delta, 3)
    v = "favourable" if delta > 0.05 else "unfavourable" if delta < -0.05 else "neutral"
    return RuleOutcome("R5_bala", "Dig Bala & Drishti Bala", applies=True,
                       delta=delta, verdict=v, reason="; ".join(parts),
                       info={"aspecting": rc.aspecting})


def r6_bhava_band(rc):
    d = rc.deg_in_sign
    if d is None:
        return RuleOutcome("R6_bhava_band", "Placement in the bhava", applies=False,
                           reason="degree unknown")
    if d <= 1.0 or d >= 29.0:
        return RuleOutcome("R6_bhava_band", "Placement in the bhava", applies=True,
                           delta=-0.4, verdict="unfavourable",
                           reason=f"bhava sandhi at {d:.1f}deg - weak/junctional")
    if 10.0 <= d <= 20.0:
        return RuleOutcome("R6_bhava_band", "Placement in the bhava", applies=True,
                           delta=0.3, verdict="favourable",
                           reason=f"bhava madhya at {d:.1f}deg - full result")
    return RuleOutcome("R6_bhava_band", "Placement in the bhava", applies=True,
                       delta=0.0, verdict="neutral",
                       reason=f"at {d:.1f}deg - partial strength")


def r7_nature(rc):
    """Natural benefic/malefic + functional (Lagna) benefic/malefic."""
    nat = "benefic" if rc.lord in NATURAL_BENEFICS else "malefic"
    delta = 0.2 if nat == "benefic" else -0.2
    parts = [f"natural {nat} ({delta:+.1f})"]

    func = _functional_nature(rc.ctx, rc.lord)
    if func == "benefic":
        fd = 0.6
    elif func == "malefic":
        fd = -0.6
    else:
        fd = 0.0
    if rc.houses_owned:
        delta += fd
        parts.append(f"functional {func or 'neutral'} ({fd:+.1f})")

    delta = round(delta, 3)
    v = "favourable" if delta > 0.05 else "unfavourable" if delta < -0.05 else "neutral"
    return RuleOutcome("R7_nature", "Natural & functional nature", applies=True,
                       delta=delta, verdict=v, reason="; ".join(parts),
                       info={"natural": nat, "functional": func})


def r8_yogas(rc):
    found = []      # (name, delta, why)

    # Raja yoga: kendra-lord <-> trikona-lord connection involving this lord.
    owns_kendra = any(h in KENDRA for h in rc.houses_owned)
    owns_trikona = any(h in TRIKONA for h in rc.houses_owned)
    if owns_kendra and rc.owns_lord_of(TRIKONA - {1}):
        found.append(("raja", 1.0, "kendra lord linked to a trikona lord (Raja yoga)"))
    elif owns_trikona and rc.owns_lord_of(KENDRA - {1}):
        found.append(("raja", 1.0, "trikona lord linked to a kendra lord (Raja yoga)"))

    # Dhana yoga: wealth-house lords linked.
    if any(h in DHANA_HOUSES for h in rc.houses_owned) and rc.owns_lord_of(DHANA_HOUSES):
        found.append(("dhana", 0.7, "wealth-house lords linked (Dhana yoga)"))

    # Vipareeta Raja yoga: a dusthana (6/8/12) lord PLACED in a dusthana house
    # (Harsha/Sarala/Vimala) - the classic placement form, not a mere link.
    if any(h in DUSTHANA for h in rc.houses_owned) and rc.house in DUSTHANA:
        found.append(("vipareeta", 0.6,
                      "dusthana lord placed in a dusthana (Vipareeta Raja yoga)"))

    # Neecha Bhanga: debilitated lord whose debilitation is cancelled.
    if rc.rasi and PLANET_DEBILITATION.get(rc.lord) == rc.rasi:
        disp = rc.dispositor
        if disp and (PLANET_EXALTATION.get(disp) == (rc.ctx.chart.get(disp) or {}).get("rasi")
                     or (rc.ctx.chart.get(disp) or {}).get("rasi") in PLANET_OWN_HOUSES.get(disp, [])):
            found.append(("neecha_bhanga", 0.7,
                          f"debilitated but dispositor {disp} strong (Neecha Bhanga)"))

    # Benefic / malefic association (conjunction or aspect).
    touch = set(rc.conjunct) | set(rc.aspecting)
    if touch & {"jupiter", "venus", "mercury"}:
        who = sorted(touch & {"jupiter", "venus", "mercury"})
        found.append(("benefic_assoc", 0.4, f"benefic association ({', '.join(who)})"))
    if touch & {"saturn", "mars", "rahu"}:
        who = sorted(touch & {"saturn", "mars", "rahu"})
        found.append(("malefic_assoc", -0.4, f"malefic association ({', '.join(who)})"))

    if not found:
        return RuleOutcome("R8_yogas", "Planetary combinations (yogas)",
                           applies=False, reason="no notable yoga/association")
    # Yogas are "very important" but must not swamp every other rule - cap swing.
    delta = round(_clamp(sum(d for _, d, _ in found), -1.6, 2.0), 3)
    v = "favourable" if delta > 0.05 else "unfavourable" if delta < -0.05 else "neutral"
    return RuleOutcome("R8_yogas", "Planetary combinations (yogas)", applies=True,
                       delta=delta, verdict=v,
                       reason="; ".join(w for _, _, w in found),
                       info={"yogas": [n for n, _, _ in found]})


def r9_conjunction_relations(rc):
    if not rc.conjunct:
        return RuleOutcome("R9_conjunction_relations", "Conjoined-planet relationship",
                           applies=False, reason="not conjunct any planet")
    rel = PLANET_RELATIONSHIPS.get(rc.lord, {})
    friends = set(rel.get("friend", []))
    enemies = set(rel.get("enemy", []))
    delta, parts = 0.0, []
    for p in rc.conjunct:
        if p in friends:
            delta += 0.15
            parts.append(f"with friend {p}")
        elif p in enemies:
            delta -= 0.15
            parts.append(f"with enemy {p}")
        else:
            parts.append(f"with neutral {p}")
    delta = round(_clamp(delta, -0.4, 0.4), 3)
    v = "favourable" if delta > 0.05 else "unfavourable" if delta < -0.05 else "neutral"
    return RuleOutcome("R9_conjunction_relations", "Conjoined-planet relationship",
                       applies=True, delta=delta, verdict=v,
                       reason="conjunct " + ", ".join(parts))


def r10_life_stage(rc):
    age = rc.ctx.current_age
    stage = life_stage_for_age(age)
    if stage is None:
        return RuleOutcome("R10_life_stage", "Life-stage the period grants",
                           applies=False, reason="birth date / age unknown")
    return RuleOutcome("R10_life_stage", "Life-stage the period grants", applies=True,
                       delta=0.0, verdict="info",
                       reason=f"acts during '{stage}' stage (age {age}) - results "
                              f"appropriate to that life phase",
                       info={"age": age, "stage": stage})


def r11b_six_eight_from_lord(rc):
    if not rc.house:
        return RuleOutcome("R11b_six_eight_from_lord", "6/8-from-lord affliction",
                           applies=False, reason="house placement unknown")
    h6 = ((rc.house + 5 - 1) % 12) + 1
    h8 = ((rc.house + 7 - 1) % 12) + 1
    tenants = [p for p in PLANETS
               if p != rc.lord and rc.ctx.planet_houses.get(p) in (h6, h8)]
    if not tenants:
        return RuleOutcome("R11b_six_eight_from_lord", "6/8-from-lord affliction",
                           applies=True, delta=0.2, verdict="favourable",
                           reason=f"no planets in the 6th/8th ({h6}th/{h8}th) from "
                                  f"{rc.lord} - unafflicted")
    malefics = [p for p in tenants if p in NATURAL_MALEFICS]
    if malefics:
        return RuleOutcome("R11b_six_eight_from_lord", "6/8-from-lord affliction",
                           applies=True, delta=-0.4, verdict="unfavourable",
                           reason=f"malefics {', '.join(malefics)} in 6th/8th from "
                                  f"{rc.lord} - afflicted")
    return RuleOutcome("R11b_six_eight_from_lord", "6/8-from-lord affliction",
                       applies=True, delta=-0.1, verdict="neutral",
                       reason=f"{', '.join(tenants)} in 6th/8th from {rc.lord}")


def r12_dispositor(rc):
    disp = rc.dispositor
    if not disp:
        return RuleOutcome("R12_dispositor", "Dispositor dignity", applies=False,
                           reason="sign lord unknown")
    disp_rasi = (rc.ctx.chart.get(disp) or {}).get("rasi")
    if disp_rasi is None:
        return RuleOutcome("R12_dispositor", "Dispositor dignity", applies=False,
                           reason=f"dispositor {disp} not placed in chart")
    if PLANET_EXALTATION.get(disp) == disp_rasi:
        return RuleOutcome("R12_dispositor", "Dispositor dignity", applies=True,
                           delta=0.6, verdict="favourable",
                           reason=f"dispositor {disp} exalted - strong support")
    if PLANET_DEBILITATION.get(disp) == disp_rasi:
        return RuleOutcome("R12_dispositor", "Dispositor dignity", applies=True,
                           delta=-0.6, verdict="unfavourable",
                           reason=f"dispositor {disp} debilitated - weak support")
    if disp_rasi in PLANET_OWN_HOUSES.get(disp, []):
        return RuleOutcome("R12_dispositor", "Dispositor dignity", applies=True,
                           delta=0.3, verdict="favourable",
                           reason=f"dispositor {disp} in own sign - steady support")
    return RuleOutcome("R12_dispositor", "Dispositor dignity", applies=True,
                       delta=0.0, verdict="neutral",
                       reason=f"dispositor {disp} in neutral dignity")


RULES = [
    r1_lagna_baseline,
    r2_stronger_than_lagna_lord,
    r3_houses_ruled,
    r4_placement,
    r5_bala,
    r6_bhava_band,
    r7_nature,
    r8_yogas,
    r9_conjunction_relations,
    r10_life_stage,
    r11b_six_eight_from_lord,
    r12_dispositor,
]


def _functional_nature(ctx, planet):
    """Classic functional (Lagna) benefic/malefic by house ownership:
    owns a trikona (1,5,9) -> benefic leaning; owns a dusthana (6,8,12) ->
    malefic leaning; the net over all houses owned decides. Nodes own no house
    -> neutral."""
    owned = [h for h, l in ctx.house_lords.items() if l == planet]
    if not owned:
        return None
    net = 0
    for h in owned:
        if h in TRIKONA:
            net += 1
        elif h in DUSTHANA:
            net -= 1
        elif h in KENDRA:
            net += 0  # kendra lordship is neutral for benefic/malefic status
    if net > 0:
        return "benefic"
    if net < 0:
        return "malefic"
    return "neutral"


def evaluate(ctx, lord, role="maha", tag=None):
    """Run all guarded rules on `lord`; only applicable ones shape the verdict.

    Anchor = the lord's own subathuvam/pabathuvam strength (0-10, current scoring
    engine). Applicable dasha-specific rules then add signed deltas. The final
    0-10 score is compared to FAVOURABLE_THRESHOLD."""
    rc = _RuleCtx(ctx, lord, role=role)
    outcomes = [rule(rc) for rule in RULES]

    anchor = rc.strength if rc.strength is not None else 5.0
    delta = sum(o.delta for o in outcomes if o.applies)
    score = round(_clamp(anchor + delta, 0.0, 10.0), 2)

    applied = [o for o in outcomes if o.applies]
    reasons = [f"[{o.verdict}] {o.reason}" for o in applied if o.verdict != "info"]
    return DasaFavourability(
        lord=lord,
        favourable=score >= FAVOURABLE_THRESHOLD,
        score=score,
        role=role,
        tag=tag,
        anchor=round(anchor, 2),
        reasons=reasons,
        findings=[o.to_dict() for o in outcomes],
    )


def _is_shashtashtaka(ctx, a, b):
    """Are lords `a` and `b` in a 6-8 relationship? Count houses from a to b;
    6 forward (=8 back) is the shashtashtaka (6-8) axis."""
    ha, hb = ctx.planet_houses.get(a), ctx.planet_houses.get(b)
    if not ha or not hb:
        return False
    fwd = ((hb - ha) % 12) + 1
    return fwd in (6, 8)


def _lords_from_active(active_dasha):
    """Parse 'Jupiter Mahadasa, Saturn Antardasa' -> ('jupiter', 'saturn').
    Returns (maha, bhukti|None) or (None, None) when unparseable."""
    if not active_dasha:
        return None, None
    maha = bhukti = None
    for part in active_dasha.split(","):
        toks = part.strip().split()
        if len(toks) < 2:
            continue
        name, kind = toks[0].lower(), toks[1].lower()
        if "maha" in kind:
            maha = name
        elif "antar" in kind or "bhukti" in kind:
            bhukti = name
    return maha, bhukti


def active_period(ctx):
    """Judge the person's CURRENT maha+bhukti period (from ctx.active_dasha).

    Returns the pair verdict, or {'available': False, ...} when no active dasha
    is known. When only a maha lord is known, judges it as a single lord."""
    maha, bhukti = _lords_from_active(ctx.active_dasha)
    if not maha:
        return {"available": False, "note": "no active dasha in context"}
    if not bhukti:
        v = evaluate(ctx, maha, role="maha", tag="ACTIVE")
        return {"available": True, "maha": v.to_dict(), "bhukti": None,
                "shashtashtaka": False, "pair_reason": ["no bhukti lord known"],
                "combined_score": v.score, "favourable": v.favourable}
    res = evaluate_period(ctx, maha, bhukti)
    res["available"] = True
    return res


def evaluate_period(ctx, maha, bhukti):
    """Judge a maha+bhukti PAIR (the user's chosen scope).

    Full rules on the maha lord AND on the bhukti lord (each vs the lagna), then
    the maha<->bhukti relationship (rule 11a shashtashtaka). Combined score
    weights the maha lord more (it sets the era) than the bhukti."""
    vm = evaluate(ctx, maha, role="maha")
    vb = evaluate(ctx, bhukti, role="bhukti")

    sixeight = _is_shashtashtaka(ctx, maha, bhukti)
    pair_reason = []
    pair_delta = 0.0
    if sixeight:
        pair_delta = -0.8
        pair_reason.append(
            f"maha {maha} and bhukti {bhukti} are 6-8 (shashtashtaka) - "
            f"unfavourable pairing")
    else:
        pair_reason.append(f"maha {maha} and bhukti {bhukti} are not 6-8")

    combined = round(_clamp(0.6 * vm.score + 0.4 * vb.score + pair_delta, 0.0, 10.0), 2)
    return {
        "maha": vm.to_dict(),
        "bhukti": vb.to_dict(),
        "shashtashtaka": sixeight,
        "pair_reason": pair_reason,
        "combined_score": combined,
        "favourable": combined >= FAVOURABLE_THRESHOLD,
    }
