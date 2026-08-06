"""
ChartContext - the single immutable object every agent reads.

Built once from the user's planet positions (+ birth date) by reusing the
existing deterministic engines (scoring, house scoring, dasha). Agents and the
rule engine only READ this; nothing mutates it.
"""

from dataclasses import dataclass
from datetime import date, datetime

from core.age_gate import compute_age, tag_timeline
from utils.calculations.dasha_calculation import (
    calculate_all_dashas_120_years,
    calculate_dasha_antardasha,
)
from utils.calculations.house_calculation import calculate_house_subathuva_pabathuvam
from utils.calculations.planet_calulation import calculate_subathuva_pabathuvam
from utils.calculations.profession_calculation import get_house_lord
from utils.calculations.utils import rasi_to_absolute_degree
from utils.constant import PLANETS
from core.point_scoring import score_chart, planet_strength_legacy
from core.house_point_scoring import score_houses, house_strength_legacy


@dataclass(frozen=True)
class ChartContext:
    ascendant_rasi: str
    chart: dict           # planet -> {rasi, house, degree}
    scores: dict          # planet -> final_score (-5..15)
    house_scores: dict    # house_num -> final_score (-5..15)
    house_lords: dict     # house_num -> planet (lowercase) | None
    planet_houses: dict   # planet -> house_num
    dashas: list          # full Vimshottari timeline (maha -> antardashas)
    tagged_periods: list  # maha periods tagged PAST/ACTIVE/UPCOMING
    active_dasha: str      # e.g. "Saturn Mahadasa, Jupiter Antardasa"
    current_age: int       # None if no birth date given
    dob: object            # datetime.date | None
    today: object          # datetime.date


def build_chart_context(data, birth_date_str=None):
    """Build a ChartContext from the /api/calculate-style input payload."""
    ascendant_rasi = data.get("ascendant", {}).get("house", "")

    # --- Scores (reuse existing engines) ---
    results = calculate_subathuva_pabathuvam(data)

    positions = {}
    if ascendant_rasi:
        positions["ascendant"] = {
            "degree": rasi_to_absolute_degree(
                ascendant_rasi, float(data["ascendant"]["degree"])
            ),
            "rasi": ascendant_rasi,
            "house": 1,
        }
    for p in PLANETS:
        if p in results:
            positions[p] = {
                "degree": results[p]["absolute_degree"],
                "rasi": results[p]["rasi"],
                "house": results[p]["house"],
            }

    house_results = calculate_house_subathuva_pabathuvam(data, results, positions)

    # Planet + house strength now come from the point-scale model (two tracks
    # collapsed onto the legacy -5..15 scale, so every downstream threshold
    # stays valid). Houses derive their strength from their lord + contacts.
    point_scores = score_chart(positions)
    house_point = score_houses(positions, ascendant_rasi)
    scores = {
        p: (planet_strength_legacy(point_scores[p]) if p in point_scores
            else results[p]["final_score"])
        for p in results
    }
    house_scores = {
        h: (house_strength_legacy(house_point[h]) if h in house_point
            else house_results[h]["final_score"])
        for h in house_results
    }
    planet_houses = {p: results[p]["house"] for p in results}
    chart = {
        p: {
            "rasi": results[p]["rasi"],
            "house": results[p]["house"],
            "degree": results[p]["absolute_degree"],
        }
        for p in results
    }
    house_lords = {
        h: (get_house_lord(h, ascendant_rasi) if ascendant_rasi else None)
        for h in range(1, 13)
    }

    # --- Dasha timeline + age (only if birth date supplied) ---
    dashas, tagged, active_dasha, dob, current_age = [], [], None, None, None
    today = date.today()

    if birth_date_str:
        try:
            dob = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
            current_age = compute_age(dob, today)
        except (ValueError, TypeError):
            dob, current_age = None, None

        moon = data.get("moon", {})
        if dob and moon.get("house") and moon.get("degree") is not None:
            moon_deg = float(moon["degree"])
            all_dashas = calculate_all_dashas_120_years(
                moon["house"], moon_deg, birth_date_str
            )
            if all_dashas:
                dashas = all_dashas.get("dashas", [])
                tagged = tag_timeline(dashas, today)

            current = calculate_dasha_antardasha(moon["house"], moon_deg, birth_date_str)
            if current and current.get("dasha"):
                lord = current["dasha"].get("lord")
                antar = current.get("current_antardasha") or {}
                antar_lord = antar.get("lord") if isinstance(antar, dict) else None
                if lord:
                    active_dasha = f"{lord.title()} Mahadasa"
                    if antar_lord:
                        active_dasha += f", {antar_lord.title()} Antardasa"

    return ChartContext(
        ascendant_rasi=ascendant_rasi,
        chart=chart,
        scores=scores,
        house_scores=house_scores,
        house_lords=house_lords,
        planet_houses=planet_houses,
        dashas=dashas,
        tagged_periods=tagged,
        active_dasha=active_dasha,
        current_age=current_age,
        dob=dob,
        today=today,
    )
