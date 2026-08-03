"""
House knowledge base - what each house actually carries.

WHY THE GOOD/BAD SPLIT MATTERS
    The rule is: when a benefic redeems a planet, the planet "only gives the
    good things which belong to that house". A redeemed 6th lord does not stop
    being a 6th lord - it stops giving the 6th house's disease and debt, and
    starts giving its victory-over-enemies and service. That is impossible to
    express with a prose string like "enemies, disease, service, debts", so
    every house declares `good` and `bad` significations separately.

    core.strength_tracks reads this: a planet whose sambandha track is
    benefic-dominated is reported as delivering `good`; one that is malefic-
    dominated delivers `bad`; a mixed one delivers both, and the LLM judge
    decides which side leads.

`events` seeds the event layer (marriage / job / accident timing). `karakas`
are the classical significator planets for that house's matters.

This is a SEED table - the quality of the reading is the quality of these
lists. Extend them freely; nothing in the engine hard-codes their contents.
"""

HOUSE_DATA = {
    1: {
        "name": "self / body",
        "good": ["health", "vitality", "confidence", "reputation", "clear identity"],
        "bad": ["illness", "low vitality", "self-doubt", "loss of standing"],
        "karakas": ["sun"],
        "people": ["self"],
        "body": ["head", "constitution"],
        "events": ["recovery", "change of appearance", "new beginning"],
    },
    2: {
        "name": "wealth / family / speech",
        "good": ["savings", "family support", "eloquence", "good food", "accumulation"],
        "bad": ["debt", "harsh speech", "family discord", "loss of savings"],
        "karakas": ["jupiter", "venus"],
        "people": ["immediate family"],
        "body": ["face", "mouth", "right eye", "throat"],
        "events": ["wealth gain", "family expansion", "financial loss"],
    },
    3: {
        "name": "courage / siblings / effort",
        "good": ["courage", "initiative", "skill", "short travel", "supportive siblings"],
        "bad": ["timidity", "conflict with siblings", "wasted effort"],
        "karakas": ["mars"],
        "people": ["younger siblings", "neighbours"],
        "body": ["arms", "shoulders", "ears"],
        "events": ["new venture", "short journey", "sibling matters"],
    },
    4: {
        "name": "home / mother / comfort",
        "good": ["property", "vehicles", "domestic peace", "education", "mother's support"],
        "bad": ["loss of property", "domestic unrest", "separation from home"],
        "karakas": ["moon", "venus"],
        "people": ["mother"],
        "body": ["chest", "heart", "lungs"],
        "events": ["property purchase", "vehicle purchase", "relocation"],
    },
    5: {
        "name": "children / intellect / merit",
        "good": ["children", "intelligence", "creativity", "romance", "past merit"],
        "bad": ["difficulty with children", "poor judgement", "speculation loss"],
        "karakas": ["jupiter"],
        "people": ["children", "students"],
        "body": ["stomach", "upper abdomen"],
        "events": ["childbirth", "romance", "creative success", "speculation"],
    },
    6: {
        "name": "enemies / disease / service",
        "good": ["victory over enemies", "competitive success", "service", "recovery",
                 "clearing debts", "discipline"],
        "bad": ["disease", "debt", "litigation", "hidden enemies", "workplace friction"],
        "karakas": ["mars", "saturn"],
        "people": ["rivals", "subordinates", "creditors"],
        "body": ["intestines", "digestion"],
        "events": ["illness", "litigation", "competitive win", "debt"],
    },
    7: {
        "name": "marriage / partnership",
        "good": ["marriage", "supportive spouse", "successful partnership", "contracts"],
        "bad": ["separation", "divorce", "partnership breakdown", "open opposition"],
        "karakas": ["venus", "jupiter"],
        "people": ["spouse", "business partner"],
        "body": ["kidneys", "lower back"],
        "events": ["marriage", "divorce", "business partnership"],
    },
    8: {
        "name": "longevity / sudden events",
        "good": ["inheritance", "occult knowledge", "research depth", "transformation",
                 "spouse's wealth"],
        "bad": ["accidents", "surgery", "chronic illness", "sudden loss", "obstruction"],
        "karakas": ["saturn"],
        "people": ["in-laws"],
        "body": ["reproductive organs", "chronic conditions"],
        "events": ["accident", "surgery", "inheritance", "sudden change"],
    },
    9: {
        "name": "fortune / dharma / father",
        "good": ["fortune", "higher learning", "long travel", "guidance", "father's support"],
        "bad": ["misfortune", "loss of faith", "estrangement from father"],
        "karakas": ["jupiter", "sun"],
        "people": ["father", "teacher", "guru"],
        "body": ["hips", "thighs"],
        "events": ["higher education", "pilgrimage", "foreign travel", "mentorship"],
    },
    10: {
        "name": "career / status / authority",
        "good": ["promotion", "recognition", "authority", "stable career", "good name"],
        "bad": ["demotion", "loss of position", "career stagnation", "public criticism"],
        "karakas": ["sun", "saturn", "mercury"],
        "people": ["employer", "government"],
        "body": ["knees", "joints"],
        "events": ["new job", "promotion", "job loss", "career shift"],
    },
    11: {
        "name": "gains / network / desires",
        "good": ["income", "fulfilment of desires", "influential friends", "elder siblings"],
        "bad": ["blocked gains", "unreliable friends", "unfulfilled ambition"],
        "karakas": ["jupiter"],
        "people": ["elder siblings", "friends", "network"],
        "body": ["calves", "ankles"],
        "events": ["income rise", "fulfilment of a long-held wish", "new network"],
    },
    12: {
        "name": "loss / expense / foreign / moksha",
        "good": ["spiritual growth", "foreign settlement", "charitable giving",
                 "productive seclusion", "restful sleep"],
        "bad": ["expenditure", "hospitalisation", "confinement", "isolation", "hidden loss"],
        "karakas": ["saturn", "ketu"],
        "people": ["foreigners", "hidden opponents"],
        "body": ["feet", "left eye", "sleep"],
        "events": ["foreign travel", "hospitalisation", "major expense", "retreat"],
    },
}

# Kept for backwards compatibility with core.dasha_rules, which imports a
# flat prose table. Derived so there is only ONE place to edit house meanings.
HOUSE_SIGNIFICATIONS = {
    h: ", ".join(d["good"][:2] + d["bad"][:2]) for h, d in HOUSE_DATA.items()
}

KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}
DUSTHANA = {6, 8, 12}
UPACHAYA = {3, 6, 10, 11}      # houses where malefics do WELL


def good_of(houses):
    """The good significations of every house in `houses`, de-duplicated."""
    out = []
    for h in houses:
        for s in HOUSE_DATA.get(h, {}).get("good", []):
            if s not in out:
                out.append(s)
    return out


def bad_of(houses):
    """The bad significations of every house in `houses`, de-duplicated."""
    out = []
    for h in houses:
        for s in HOUSE_DATA.get(h, {}).get("bad", []):
            if s not in out:
                out.append(s)
    return out


def name_of(house):
    return HOUSE_DATA.get(house, {}).get("name", f"{ordinal(house)} house")


def ordinal(n):
    """1 -> '1st', 2 -> '2nd', 11 -> '11th'. These strings go into the LLM
    prompt and into user-facing reasons, so '2th' is not acceptable."""
    if n is None:
        return "?"
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"
