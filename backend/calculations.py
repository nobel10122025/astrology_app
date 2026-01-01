"""
Vedic Astrology Calculations for Subathuva and Pabathuvam
Main module that re-exports all calculation functions
"""

# Import all functions from sub-modules
from utils.calculations.utils import (
    rasi_to_absolute_degree,
    normalize_degree,
    calculate_degree_difference,
    get_conjunction_level,
    get_aspect_degrees,
    check_aspect,
    is_combust,
    get_house_number,
    calculate_moon_position_effect
)

from utils.calculations.planet_calulation import (
    calculate_subathuva_pabathuvam
)

from utils.calculations.house_calculation import (
    calculate_house_subathuva_pabathuvam
)

from utils.calculations.profession_calculation import (
    get_house_lord,
    is_planet_connected_to_house_lord,
    calculate_professions
)

from utils.calculations.dasha_calculation import (
    get_nakshatra_from_degree,
    calculate_dasha_remaining,
    calculate_antardashas,
    calculate_dasha_antardasha
)

# Re-export all functions for backward compatibility
__all__ = [
    # Utility functions
    'rasi_to_absolute_degree',
    'normalize_degree',
    'calculate_degree_difference',
    'get_conjunction_level',
    'get_aspect_degrees',
    'check_aspect',
    'is_combust',
    'get_house_number',
    'calculate_moon_position_effect',
    # Planet calculations
    'calculate_subathuva_pabathuvam',
    # House calculations
    'calculate_house_subathuva_pabathuvam',
    # Profession calculations
    'get_house_lord',
    'is_planet_connected_to_house_lord',
    'calculate_professions',
    # Dasha calculations
    'get_nakshatra_from_degree',
    'calculate_dasha_remaining',
    'calculate_antardashas',
    'calculate_dasha_antardasha',
]
