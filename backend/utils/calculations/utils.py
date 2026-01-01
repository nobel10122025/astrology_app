"""
Utility functions for Vedic Astrology Calculations
"""

from utils.constant import RASI_TO_DEGREE, PLANET_EXALTATION, PLANET_DEBILITATION, PLANET_OWN_HOUSES, PLANET_RELATIONSHIPS, PLANETS, DRIK_BALAM_LOGIC, COMBUST_DEGREES


def rasi_to_absolute_degree(rasi, degree_in_sign):
    """Convert rasi and degree to absolute degree (0-360)"""
    if rasi not in RASI_TO_DEGREE:
        return None
    base_degree, _ = RASI_TO_DEGREE[rasi]
    return base_degree + float(degree_in_sign)


def normalize_degree(degree):
    """Normalize degree to 0-360 range"""
    while degree < 0:
        degree += 360
    while degree >= 360:
        degree -= 360
    return degree


def calculate_degree_difference(deg1, deg2):
    """Calculate minimum degree difference between two degrees"""
    diff = abs(deg1 - deg2)
    if diff > 180:
        diff = 360 - diff
    return diff


def get_conjunction_level(degree_diff):
    """Determine conjunction level based on degree difference"""
    if degree_diff < 7:
        return 'very_high'
    elif degree_diff < 13:
        return 'high'
    elif degree_diff < 17:
        return 'medium'
    elif degree_diff < 23:
        return 'less'
    else:
        return 'none'


def get_aspect_degrees(planet, planet_degree):
    """Get aspect degrees for a planet"""
    aspects = []
    
    if planet in ['venus', 'moon', 'mercury', 'sun']:
        # 180° aspect
        aspects.append(normalize_degree(planet_degree + 180))
    
    elif planet == 'jupiter':
        # 120°, 180°, 240°
        aspects.extend([
            normalize_degree(planet_degree + 120),
            normalize_degree(planet_degree + 180),
            normalize_degree(planet_degree + 240)
        ])
    
    elif planet == 'saturn':
        # 60°, 180°, 270°
        aspects.extend([
            normalize_degree(planet_degree + 60),
            normalize_degree(planet_degree + 180),
            normalize_degree(planet_degree + 270)
        ])
    
    elif planet == 'mars':
        # 120°, 180°, 210°
        aspects.extend([
            normalize_degree(planet_degree + 90),
            normalize_degree(planet_degree + 180),
            normalize_degree(planet_degree + 210)
        ])
    
    # Rahu and Ketu have no aspects
    return aspects


def check_aspect(planet, planet_degree, target_degree):
    """Check if planet aspects target degree and return level"""
    aspects = get_aspect_degrees(planet, planet_degree)
    
    if not aspects:
        return 'none'
    
    # Find the minimum difference across all aspects
    min_diff = 360
    for aspect_degree in aspects:
        diff = calculate_degree_difference(aspect_degree, target_degree)
        min_diff = min(min_diff, diff)
    
    if min_diff <= 5:
        return 'high'
    elif min_diff <= 10:
        return 'medium'
    elif min_diff <= 13:
        return 'negligible'
    else:
        return 'none'


def is_combust(planet_degree, sun_degree, combust_degree):
    """Check if planet is combust (close to sun)"""
    if combust_degree is None:
        return "none"
    
    diff = calculate_degree_difference(planet_degree, sun_degree)
    if diff <= 3: return "high"
    elif diff <= combust_degree: return "low"
    return "none"


def get_house_number(ascendant_rasi, planet_rasi):
    """Calculate house number (1-12) based on ascendant"""
    rasi_list = list(RASI_TO_DEGREE.keys())
    asc_index = rasi_list.index(ascendant_rasi)
    planet_index = rasi_list.index(planet_rasi)
    
    house = ((planet_index - asc_index) % 12) + 1
    return house


def calculate_moon_position_effect(positions):
    """
    Calculate Moon position effect based on Sun-Moon difference
    Returns a dictionary with effect details
    """
    if 'sun' not in positions or 'moon' not in positions:
        return None
    
    sun_degree = positions['sun']['degree']
    moon_degree = positions['moon']['degree']
    moon_house = positions['moon']['house']
    
    # Calculate absolute difference
    degree_diff = calculate_degree_difference(sun_degree, moon_degree)
    
    effect = {
        'multiplier': 0,
        'type': 'none',
        'degree_diff': degree_diff,
        'moon_house': moon_house
    }
    
    # Determine multiplier based on degree difference
    if 0 <= degree_diff < 45:
        effect['multiplier'] = 0
        effect['type'] = 'pabathuvam'
    elif 45 <= degree_diff < 90:
        effect['multiplier'] = 0.5
        effect['type'] = 'subathuva'
    elif 90 <= degree_diff < 135:
        effect['multiplier'] = 1
        effect['type'] = 'subathuva'
    elif 135 <= degree_diff <= 180:
        effect['multiplier'] = 2
        effect['type'] = 'subathuva'
        effect['special_case'] = True
    else:
        # For > 180, we can wrap it or handle differently
        # Since we use absolute difference, this shouldn't happen, but handle it
        effect['multiplier'] = 0
        effect['type'] = 'none'
    
    return effect

