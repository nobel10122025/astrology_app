"""
Profession calculation functions
"""

from utils.constant import RASI_TO_DEGREE, PLANET_OWN_HOUSES
from utils.calculations.utils import (
    calculate_degree_difference, get_conjunction_level, check_aspect, get_aspect_degrees
)


def get_house_lord(house_num, ascendant_rasi):
    """Get the planet that owns the rasi in the given house"""
    rasi_list = list(RASI_TO_DEGREE.keys())
    asc_index = rasi_list.index(ascendant_rasi)
    rasi_index = (asc_index + house_num - 1) % 12
    house_rasi = rasi_list[rasi_index]
    
    # Find which planet owns this rasi
    for planet, owned_rasi_list in PLANET_OWN_HOUSES.items():
        if house_rasi in owned_rasi_list:
            return planet
    return None


def is_planet_connected_to_house_lord(planet, house_lord, positions):
    """Check if planet is connected to house lord (present at, aspects, or is the house lord)"""
    if planet == house_lord:
        return True, "is the house lord"
    
    if house_lord not in positions:
        return False, ""
    
    planet_pos = positions[planet]
    lord_pos = positions[house_lord]
    
    # Check if planet is in same house as house lord (conjunction)
    if planet_pos['house'] == lord_pos['house']:
        degree_diff = calculate_degree_difference(planet_pos['degree'], lord_pos['degree'])
        conj_level = get_conjunction_level(degree_diff)
        if conj_level != 'none':
            return True, f"conjuncted with {house_lord.upper()}"
    
    # Check if planet aspects house lord
    aspect_level = check_aspect(planet, planet_pos['degree'], lord_pos['degree'])
    if aspect_level != 'none':
        return True, f"aspects {house_lord.upper()}"
    
    return False, ""


def calculate_professions(data, planet_results, positions, house_results):
    """Calculate professions based on subathuva planets and house connectivity"""
    ascendant_rasi = data.get('ascendant', {}).get('house', '')
    if not ascendant_rasi:
        return None
    
    # Get house lords for 2nd, 10th, and 11th houses
    house_2_lord = get_house_lord(2, ascendant_rasi)
    house_10_lord = get_house_lord(10, ascendant_rasi)
    house_11_lord = get_house_lord(11, ascendant_rasi)
    
    # Get Moon position
    moon_house = positions.get('moon', {}).get('house') if 'moon' in positions else None
    moon_2nd_house = ((moon_house + 1) % 12) or 12 if moon_house else None
    moon_10th_house = ((moon_house + 9) % 12) or 12 if moon_house else None
    
    # Step 1: Get first two subathuva planets (sorted by final_score descending)
    subathuva_planets = []
    for planet_name, result in planet_results.items():
        if result['final_score'] > 5:  # Subathuva planets have score > 5
            subathuva_planets.append({
                'planet': planet_name,
                'score': result['final_score'],
                'house': result['house']
            })
    
    # Sort by score descending
    subathuva_planets.sort(key=lambda x: x['score'], reverse=True)
    top_subathuva_planets = subathuva_planets[:2]
    
    # Step 2: Find profession-determining planet based on connectivity rules
    profession_planet = None
    connection_reason = ""
    
    if len(top_subathuva_planets) >= 1:
        # If more than one planet is subathuvam, find planet connected to 2nd and 10th house lord
        if len(top_subathuva_planets) > 1:
            common_planet = None
            for planet_info in top_subathuva_planets:
                planet = planet_info['planet']
                connected_2nd, reason_2nd = is_planet_connected_to_house_lord(planet, house_2_lord, positions)
                connected_10th, reason_10th = is_planet_connected_to_house_lord(planet, house_10_lord, positions)
                
                if connected_2nd and connected_10th:
                    common_planet = planet
                    connection_reason = f"Connected to both 2nd lord ({house_2_lord.upper()}) and 10th lord ({house_10_lord.upper()})"
                    break
            
            if common_planet:
                profession_planet = common_planet
            else:
                # If no common planet, consider planet associated with 10th lord
                for planet_info in top_subathuva_planets:
                    planet = planet_info['planet']
                    connected_10th, reason_10th = is_planet_connected_to_house_lord(planet, house_10_lord, positions)
                    if connected_10th:
                        profession_planet = planet
                        connection_reason = f"Connected to 10th lord ({house_10_lord.upper()}) - {reason_10th}"
                        break
        else:
            # If only one subathuva planet, check if it's connected to 10th lord
            if top_subathuva_planets:
                planet = top_subathuva_planets[0]['planet']
                connected_10th, reason_10th = is_planet_connected_to_house_lord(planet, house_10_lord, positions)
                if connected_10th:
                    profession_planet = planet
                    connection_reason = f"Connected to 10th lord ({house_10_lord.upper()}) - {reason_10th}"
                else:
                    # Use the top subathuva planet anyway
                    profession_planet = planet
                    connection_reason = f"Top subathuva planet"
    
    # Step 3: If no planet with highest subathuvam connected with 10th house
    if not profession_planet:
        # Consider planets associated with 10th house (present at, aspects it, or house lord)
        house_10_rasi = None
        if ascendant_rasi:
            rasi_list = list(RASI_TO_DEGREE.keys())
            asc_index = rasi_list.index(ascendant_rasi)
            rasi_index = (asc_index + 9) % 12  # 10th house
            house_10_rasi = rasi_list[rasi_index]
        
        # Check planets in 10th house
        for planet_name, result in planet_results.items():
            if result['house'] == 10:
                profession_planet = planet_name
                connection_reason = f"Present in 10th house"
                break
        
        # Check planets aspecting 10th house
        if not profession_planet and house_10_rasi:
            house_10_center = RASI_TO_DEGREE[house_10_rasi][0] + 15
            for planet_name, result in planet_results.items():
                planet_pos = positions.get(planet_name)
                if planet_pos:
                    aspects = get_aspect_degrees(planet_name, planet_pos['degree'])
                    for aspect_degree in aspects:
                        diff = calculate_degree_difference(aspect_degree, house_10_center)
                        if diff <= 15:
                            profession_planet = planet_name
                            connection_reason = f"Aspects 10th house"
                            break
                if profession_planet:
                    break
        
        # Check 10th house lord
        if not profession_planet and house_10_lord:
            if house_10_lord in planet_results:
                profession_planet = house_10_lord
                connection_reason = f"Is the 10th house lord"
    
    # Step 4: Consider planets from 2nd and 10th house from MOON
    moon_related_planets = []
    if moon_house:
        for planet_name, result in planet_results.items():
            if result['house'] == moon_2nd_house or result['house'] == moon_10th_house:
                moon_related_planets.append({
                    'planet': planet_name,
                    'score': result['final_score'],
                    'house': result['house'],
                    'from_moon': '2nd' if result['house'] == moon_2nd_house else '10th'
                })
    
    # Step 5: Consider 2 or 3 houses subathuvam that coincide with 2nd, 10th, and 11th house
    subathuva_houses = []
    for house_num in [2, 10, 11]:
        if house_num in house_results:
            house_result = house_results[house_num]
            if house_result['final_score'] >= 6:  # Subathuva house
                house_lord = get_house_lord(house_num, ascendant_rasi)
                subathuva_houses.append({
                    'house': house_num,
                    'score': house_result['final_score'],
                    'lord': house_lord
                })
    
    # Prepare data for AI
    profession_data = {
        'top_subathuva_planets': top_subathuva_planets,
        'profession_planet': profession_planet,
        'connection_reason': connection_reason,
        'house_2_lord': house_2_lord,
        'house_10_lord': house_10_lord,
        'house_11_lord': house_11_lord,
        'moon_related_planets': moon_related_planets,
        'subathuva_houses': subathuva_houses,
        'moon_2nd_house': moon_2nd_house,
        'moon_10th_house': moon_10th_house
    }
    
    return profession_data

