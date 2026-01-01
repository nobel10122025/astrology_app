"""
House calculation functions for Subathuva and Pabathuvam
"""

from utils.constant import RASI_TO_DEGREE, PLANETS
from utils.calculations.utils import (
    calculate_moon_position_effect, get_aspect_degrees, calculate_degree_difference
)


def calculate_house_subathuva_pabathuvam(data, planet_results, positions):
    """Calculate Subathuva and Pabathuvam for each house"""
    ascendant_rasi = data.get('ascendant', {}).get('house', '')
    if not ascendant_rasi:
        return {}
    
    # Process Moon position logic first (before other calculations)
    moon_effect = calculate_moon_position_effect(positions)
    
    house_results = {}
    
    # Get rasi for each house
    rasi_list = list(RASI_TO_DEGREE.keys())
    asc_index = rasi_list.index(ascendant_rasi)
    house_rasi_map = {}
    for i in range(1, 13):
        rasi_index = (asc_index + i - 1) % 12
        house_rasi_map[i] = rasi_list[rasi_index]
    
    # Calculate house center degree for aspect calculations
    house_center_degrees = {}
    for house_num in range(1, 13):
        rasi = house_rasi_map[house_num]
        base_degree, _ = RASI_TO_DEGREE[rasi]
        house_center_degrees[house_num] = base_degree + 15  # Center of the house
    
    # Calculate for each house
    for house_num in range(1, 13):
        base_score = 5
        breakdown = {
            'base': {'value': 5, 'reason': 'Base score for all houses'},
            'subathuva': {'value': 0, 'reason': 'Benefic influences from planets in house and aspects'},
            'pabathuvam': {'value': 0, 'reason': 'Malefic influences from planets in house and aspects'},
            'planets_in_house': {'value': 0, 'reason': 'Number of planets placed in this house'},
            'benefic_aspects': {'value': 0, 'reason': 'Benefic aspects (Jupiter, Venus, Mercury) to this house'},
            'malefic_aspects': {'value': 0, 'reason': 'Malefic aspects (Saturn, Mars) to this house'}
        }
        
        subathuva_reasons = []
        pabathuvam_reasons = []
        planets_in_house_list = []
        
        subathuva_points = 0
        pabathuvam_points = 0
        
        # 1. Planets placed in the house
        planets_in_house = []
        for planet in PLANETS:
            if planet in positions:
                if positions[planet]['house'] == house_num:
                    planets_in_house.append(planet)
                    breakdown['planets_in_house']['value'] += 1
                    planets_in_house_list.append(planet.upper())
                    
                    # Benefic planets in house add Subathuva
                    if planet in ['jupiter', 'venus', 'mercury']:
                        subathuva_points += 1
                        subathuva_reasons.append(f"{planet.upper()} placed in house (+1)")
                    # Malefic planets in house add Pabathuvam
                    elif planet in ['saturn', 'mars']:
                        pabathuvam_points += 1
                        pabathuvam_reasons.append(f"{planet.upper()} placed in house (-1)")
                    elif planet == 'rahu':
                        pabathuvam_points += 1
                        pabathuvam_reasons.append("RAHU placed in house (-1)")
        
        if planets_in_house_list:
            breakdown['planets_in_house']['reason'] = f"Planets in house: {', '.join(planets_in_house_list)}"
        else:
            breakdown['planets_in_house']['reason'] = 'No planets in this house'
        
        # 2. Aspect Analysis - Check which planets aspect this house
        house_center = house_center_degrees[house_num]
        house_rasi = house_rasi_map[house_num]
        
        # First, collect all planets that aspect this house
        planets_aspecting = []
        for planet in PLANETS:
            if planet not in positions:
                continue
            
            planet_pos = positions[planet]
            planet_degree = planet_pos['degree']
            
            # Check if planet aspects this house (simple boolean check)
            aspects = get_aspect_degrees(planet, planet_degree)
            has_aspect = False
            if aspects:
                for aspect_degree in aspects:
                    diff = calculate_degree_difference(aspect_degree, house_center)
                    if diff <= 15:  # Within aspect range
                        has_aspect = True
                        break
            
            if has_aspect:
                planets_aspecting.append(planet)
        
        # Now process aspects with special rule for Leo
        for planet in planets_aspecting:
            planet_pos = positions[planet]
            
            # Benefic aspects
            if planet in ['jupiter', 'venus', 'mercury']:
                subathuva_points += 1
                breakdown['benefic_aspects']['value'] += 1
                subathuva_reasons.append(f"Aspect from {planet.upper()} (+1)")
            
            # Malefic aspects (Saturn, Mars)
            if planet in ['saturn', 'mars']:
                # Special rule: If Leo (simha) has aspect from only Mars (not Saturn), don't count as Pabathuvam
                if house_rasi == 'simha' and planet == 'mars':
                    # Check if Saturn also aspects this house
                    saturn_aspects = 'saturn' in planets_aspecting
                    if not saturn_aspects:
                        # Only Mars aspects Leo, skip Pabathuvam
                        pabathuvam_points += 0
                        pabathuvam_reasons.append(f"Aspect from {planet.upper()} (0)")
                        continue
                
                pabathuvam_points += 1
                breakdown['malefic_aspects']['value'] += 1
                pabathuvam_reasons.append(f"Aspect from {planet.upper()} (-1)")
        
        # 3. Moon Position Effect - Apply if Moon is in house or aspects the house
        if moon_effect and 'moon' in positions:
            moon_pos = positions['moon']
            moon_house = moon_pos['house']
            moon_degree = moon_pos['degree']
            
            # Check if Moon is placed in this house
            moon_in_house = (moon_house == house_num)
            
            # Check if Moon aspects this house
            house_center = house_center_degrees[house_num]
            moon_aspects_house = False
            aspects = get_aspect_degrees('moon', moon_degree)
            if aspects:
                for aspect_degree in aspects:
                    diff = calculate_degree_difference(aspect_degree, house_center)
                    if diff <= 13:  # Within aspect range
                        moon_aspects_house = True
                        break
            
            # Apply Moon position effect if Moon is in house or aspects the house
            if moon_in_house or moon_aspects_house:
                multiplier = moon_effect['multiplier']
                effect_type = moon_effect['type']
                
                if effect_type == 'pabathuvam' and multiplier == 0:
                    # 0-45°: add to pabathuvam
                    pabathuvam_points += 1
                    connection_type = "placed in house" if moon_in_house else "aspects house"
                    pabathuvam_reasons.append(f"Moon position effect (0-45° from Sun) - Moon {connection_type}: Pabathuvam (+1)")
                elif effect_type == 'subathuva':
                    # 45-90° (0.5), 90-135° (1), or 135-180° (2): add to subathuva
                    subathuva_points += multiplier
                    connection_type = "placed in house" if moon_in_house else "aspects house"
                    subathuva_reasons.append(f"Moon position effect ({moon_effect['degree_diff']:.1f}° from Sun) - Moon {connection_type}: Subathuva (+{multiplier})")
        
        breakdown['subathuva'] = {'value': subathuva_points, 'reason': '; '.join(subathuva_reasons) if subathuva_reasons else 'No benefic influences'}
        breakdown['pabathuvam'] = {'value': -pabathuvam_points, 'reason': '; '.join(pabathuvam_reasons) if pabathuvam_reasons else 'No malefic influences'}
        
        # Ensure all breakdown values are objects
        for key in ['benefic_aspects', 'malefic_aspects']:
            if isinstance(breakdown[key], (int, float)):
                breakdown[key] = {'value': breakdown[key], 'reason': 'No specific reason'}
        
        # Calculate final score
        final_score = (
            base_score +
            subathuva_points
        ) - pabathuvam_points
        
        # Clamp between -5 and 15
        final_score = max(-5, min(15, final_score))
        
        house_results[house_num] = {
            'house': house_num,
            'rasi': house_rasi_map[house_num],
            'final_score': round(final_score, 2),
            'breakdown': breakdown,
            'planets_in_house': planets_in_house
        }
    
    return house_results

