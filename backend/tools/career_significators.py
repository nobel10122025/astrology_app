"""
Tool: career_significators.

WHO shapes the career - the planets connected (in any way) to the career houses,
ranked by strength. Wraps ChartQuery's connection operator.
"""

from core.chart_query import ChartQuery
from utils.constant import PLANET_PROFESSIONS

NAME = "career_significators"


def run(ctx, career_houses=(10, 2)):
    """Returns:
        {
          "connected": {planet: {house: [OCCUPIES|OWNS|ASPECTS]}},
          "ranked": [planets with a profession list, strongest first],
          "career_planets": [top 3 connected planets, for the field resolver],
        }
    """
    q = ChartQuery(ctx)
    connected = q.planets_connected_to_group(list(career_houses))
    ranked = [p for p in connected if p in PLANET_PROFESSIONS]
    ranked.sort(key=lambda p: ctx.scores.get(p, 0), reverse=True)
    return {
        "connected": connected,
        "ranked": ranked,
        "career_planets": list(connected)[:3],
    }
