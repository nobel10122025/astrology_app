"""
ChartQuery - the reusable "significators + connections" engine.

This is the piece that makes recipe-driven agents possible. A question does not
map to a fixed list of rules; it maps to a set of SIGNIFICATORS (which houses,
lords, occupants, karakas matter) plus CONNECTION queries ("is house A linked to
house B in any way?"). The significators are finite and declared per agent; the
connection logic is generic and lives here, written once and reused by every
agent.

Nothing here computes narrative or verdicts. It only answers structural
questions about an immutable ChartContext:

    q = ChartQuery(ctx)
    q.lord(7)                      -> lord of the 7th house
    q.occupants(10)               -> planets sitting in the 10th
    q.karakas("marriage")         -> ["venus"]
    q.connections("saturn", 10)   -> ["OWNS", "ASPECTS"]  (how Saturn touches 10)
    q.planets_connected_to(10)    -> {"saturn": ["OWNS"], "sun": ["OCCUPIES"], ...}
    q.activators_of([3, 7, 11])   -> {planets that time that house group}  -> timing
"""

from utils.constant import PLANETS

# Classical karakas (significators) per topic. A karaka is a planet that stands
# for a life area regardless of house - e.g. Venus signifies marriage/spouse for
# everyone. Agents ask for these by topic instead of hard-coding planet names.
KARAKAS = {
    "marriage": ["venus"],
    "spouse": ["venus"],
    "career": ["sun", "saturn", "mercury"],
    "profession": ["sun", "saturn", "mercury"],
    "wealth": ["jupiter", "venus"],
    "children": ["jupiter"],
    "education": ["mercury", "jupiter"],
    "health": ["sun"],
    "father": ["sun"],
    "mother": ["moon"],
    "siblings": ["mars"],
}

# House-based graha drishti (aspect by house count from the planet's house).
# Every planet aspects the 7th from itself; the outer malefics + Jupiter have
# extra special aspects. Rahu/Ketu are left with no aspect to stay consistent
# with the existing scoring engine (get_aspect_degrees returns none for them).
# Values are house offsets counted inclusively (7 = the opposite house).
_ASPECT_HOUSES = {
    "mars": (4, 7, 8),
    "jupiter": (5, 7, 9),
    "saturn": (3, 7, 10),
    "sun": (7,),
    "moon": (7,),
    "mercury": (7,),
    "venus": (7,),
    # rahu / ketu: none
}


def _aspected_houses(from_house, planet):
    """Houses aspected by `planet` sitting in `from_house` (1-based, wraps)."""
    offsets = _ASPECT_HOUSES.get(planet, ())
    houses = set()
    for n in offsets:
        houses.add(((from_house - 1 + (n - 1)) % 12) + 1)
    return houses


class ChartQuery:
    """A thin, read-only lens over a ChartContext. Cheap to construct; holds no
    state beyond the context reference."""

    def __init__(self, ctx):
        self.ctx = ctx

    # --- basic lookups -----------------------------------------------------
    def house_of(self, planet):
        return self.ctx.planet_houses.get(planet)

    def lord(self, house):
        """The lord (ruling planet) of a house, lowercase, or None."""
        return self.ctx.house_lords.get(house)

    def occupants(self, house):
        """Planets sitting in a house, strongest first."""
        planets = [p for p, h in self.ctx.planet_houses.items() if h == house]
        planets.sort(key=lambda p: self.ctx.scores.get(p, 0), reverse=True)
        return planets

    def lagna_lord(self):
        return self.lord(1)

    def karakas(self, topic):
        """Significator planets for a topic (e.g. 'marriage' -> ['venus'])."""
        return list(KARAKAS.get(topic.lower(), []))

    def strength(self, entity):
        """Normalized 0-10 strength for a planet or a house number.
        Raw scores live on the -5..15 scale used by the engine."""
        if isinstance(entity, int):
            raw = self.ctx.house_scores.get(entity)
        else:
            raw = self.ctx.scores.get(entity)
        if raw is None:
            return None
        return round(max(0.0, min(10.0, (raw + 5) * 0.5)), 2)

    # --- aspects -----------------------------------------------------------
    def aspects_house(self, planet, house):
        """True if `planet` casts a house-based aspect onto `house`."""
        ph = self.house_of(planet)
        if ph is None:
            return False
        return house in _aspected_houses(ph, planet)

    def aspects_planet(self, planet, target):
        """True if `planet` aspects the house occupied by `target` planet."""
        th = self.house_of(target)
        return th is not None and self.aspects_house(planet, th)

    # --- the connection operator ("in any way") ----------------------------
    def connections(self, planet, house):
        """How is `planet` connected to `house`? Returns the list of link kinds:
        OCCUPIES (sits in it), OWNS (is its lord), ASPECTS (casts a drishti).
        Empty list = no connection."""
        links = []
        if self.house_of(planet) == house:
            links.append("OCCUPIES")
        if self.lord(house) == planet:
            links.append("OWNS")
        if self.aspects_house(planet, house):
            links.append("ASPECTS")
        return links

    def planets_connected_to(self, house, planets=None):
        """Every planet connected to `house` in any way -> {planet: [kinds]}.
        Ordered strongest planet first."""
        pool = planets if planets is not None else PLANETS
        out = {}
        for p in pool:
            kinds = self.connections(p, house)
            if kinds:
                out[p] = kinds
        return dict(
            sorted(out.items(), key=lambda kv: self.ctx.scores.get(kv[0], 0), reverse=True)
        )

    def planets_connected_to_group(self, houses, planets=None):
        """Planets that touch ANY house in the group -> {planet: {house: [kinds]}}.
        This is the "connection of 3rd-7th-11th in any way" primitive."""
        pool = planets if planets is not None else PLANETS
        out = {}
        for p in pool:
            per_house = {}
            for h in houses:
                kinds = self.connections(p, h)
                if kinds:
                    per_house[h] = kinds
            if per_house:
                out[p] = per_house
        return dict(
            sorted(out.items(), key=lambda kv: self.ctx.scores.get(kv[0], 0), reverse=True)
        )

    def activators_of(self, houses):
        """Planets whose dasha/antardasha can 'fire' this group of houses: the
        lords of those houses plus any planet connected to them. This set feeds
        the TimingResolver to place the event in an age window."""
        activators = set()
        for h in houses:
            lord = self.lord(h)
            if lord:
                activators.add(lord)
        activators.update(self.planets_connected_to_group(houses).keys())
        return activators
