"""
Planet calculation functions for Subathuva and Pabathuvam
"""

from utils.constant import PLANET_EXALTATION, PLANET_DEBILITATION, PLANET_OWN_HOUSES, PLANET_RELATIONSHIPS, PLANETS, DRIK_BALAM_LOGIC, COMBUST_DEGREES
from utils.calculations.utils import (
    rasi_to_absolute_degree, get_house_number, calculate_moon_position_effect,
    calculate_degree_difference, get_conjunction_level, check_aspect, is_combust
)


def calculate_subathuva_pabathuvam(data):
    """Main calculation function for planets"""
    # Convert all positions to absolute degrees
    positions = {}
    ascendant_rasi = data.get('ascendant', {}).get('house', '')
    
    # Process ascendant
    if ascendant_rasi:
        asc_degree = rasi_to_absolute_degree(
            ascendant_rasi,
            float(data.get('ascendant', {}).get('degree', 0))
        )
        positions['ascendant'] = {
            'degree': asc_degree,
            'rasi': ascendant_rasi,
            'house': 1
        }
    
    # Process planets
    for planet in PLANETS:
        planet_data = data.get(planet, {})
        if planet_data.get('house') and planet_data.get('degree'):
            rasi = planet_data['house']
            degree_in_sign = float(planet_data['degree'])
            abs_degree = rasi_to_absolute_degree(rasi, degree_in_sign)
            
            if abs_degree is not None and ascendant_rasi:
                house_num = get_house_number(ascendant_rasi, rasi)
                positions[planet] = {
                    'degree': abs_degree,
                    'rasi': rasi,
                    'house': house_num,
                    'degree_in_sign': degree_in_sign
                }
    
    # Process Moon position logic first (before other calculations)
    moon_effect = calculate_moon_position_effect(positions)
    
    # Calculate results for each planet
    results = {}
    
    for planet in PLANETS:
        if planet not in positions:
            continue
        
        planet_pos = positions[planet]
        base_score = 5
        breakdown = {
            'base': {'value': 5, 'reason': 'Base score for all planets'},
            'subathuva': {'value': 0, 'reason': 'Benefic influences from conjunctions and aspects'},
            'pabathuvam': {'value': 0, 'reason': 'Malefic influences from conjunctions and aspects'},
            'position': {'value': 0, 'reason': 'Planet in its own house'},
            'exaltation_debilitation': {'value': 0, 'reason': 'Planet in exaltation or debilitation sign'},
            'friendship': {'value': 0, 'reason': 'Relationship with sign lord (friend/enemy/neutral)'},
            'special_houses': {'value': 0, 'reason': 'Planet in Kendras (1,4,7,10) or Trikonas (1,5,9)'},
            'drik_balam': {'value': 0, 'reason': 'Planet in Drik Balam (gain/loss/neutral)'},
            'exalt_debil_conjunction': {'value': 0, 'reason': 'Conjunction between exalted and debilitated planets'},
            'planetery_exchange': {'value': 0, 'reason': 'Planetery exchange between planets'},
            'combust': {'value': 0, 'reason': 'Planet too close to Sun (combustion)'}
        }
        
        # Track reasons for subathuva and pabathuvam
        subathuva_reasons = []
        pabathuvam_reasons = []
        
        # 1. Conjunction Analysis (only planets, not ascendant)
        subathuva_points = 0
        pabathuvam_points = 0
        
        for other_planet in PLANETS:
            if other_planet == planet or other_planet not in positions:
                continue
            
            other_pos = positions[other_planet]
            degree_diff = calculate_degree_difference(
                planet_pos['degree'],
                other_pos['degree']
            )
            conj_level = get_conjunction_level(degree_diff)
            
            if conj_level == 'none':
                continue
            
            # Benefic planets (Jupiter, Venus, Mercury)
            if other_planet in ['jupiter', 'venus', 'mercury']:
                if conj_level in ['very_high', 'high']:
                    subathuva_points += 2
                    subathuva_reasons.append(f"High/Very High conjunction with {other_planet.upper()} (+2)")
                elif conj_level in ['medium', 'less']:
                    subathuva_points += 1
                    subathuva_reasons.append(f"Medium/Less conjunction with {other_planet.upper()} (+1)")
            
            # Malefic planets (Saturn, Mars)
            if other_planet in ['saturn', 'mars']:
                if conj_level in ['very_high', 'high']:
                    pabathuvam_points += 2
                    pabathuvam_reasons.append(f"High/Very High conjunction with {other_planet.upper()} (-2)")
                elif conj_level in ['medium', 'less']:
                    pabathuvam_points += 1
                    pabathuvam_reasons.append(f"Medium/Less conjunction with {other_planet.upper()} (-1)")
            
            # Rahu conjunction
            if other_planet == 'rahu':
                if conj_level in ['very_high', 'high']:
                    pabathuvam_points += 2
                    pabathuvam_reasons.append(f"High/Very High conjunction with RAHU (-2)")
                elif conj_level in ['medium', 'less']:
                    pabathuvam_points += 1
                    pabathuvam_reasons.append(f"Medium/Less conjunction with RAHU (-1)")
            
            # Sun conjunction (neither subathuva nor pabathuvam, but check combust)
            if other_planet == 'sun':
                combust_degree = COMBUST_DEGREES[planet] if planet in COMBUST_DEGREES else None
                combust_level = is_combust(planet_pos['degree'], other_pos['degree'], combust_degree)
                if combust_degree and combust_level == "high":
                    pabathuvam_points += 2
                    breakdown['combust'] = {'value': -2, 'reason': f'Planet is combust (within {combust_degree}° of Sun)'}
                    pabathuvam_reasons.append("Combustion with Sun (-2)")
                elif combust_degree and combust_level == "low":
                    pabathuvam_points += 1
                    breakdown['combust'] = {'value': -1, 'reason': f'Planet is combust (within {combust_degree}° of Sun)'}
                    pabathuvam_reasons.append("Combustion with Sun (-1)")
        
        # 2. Aspect Analysis
        for other_planet in PLANETS:
            if other_planet == planet or other_planet not in positions:
                continue
            
            other_pos = positions[other_planet]
            
            # Check if other planet aspects this planet
            aspect_level = check_aspect(
                other_planet,
                other_pos['degree'],
                planet_pos['degree']
            )
            
            if aspect_level == 'none':
                continue
            
            # Benefic aspects
            if other_planet in ['jupiter', 'venus', 'mercury']:
                if aspect_level == 'high':
                    subathuva_points += 2
                    subathuva_reasons.append(f"High aspect from {other_planet.upper()} (+2)")
                elif aspect_level in ['medium', 'negligible']:
                    subathuva_points += 1
                    subathuva_reasons.append(f"Medium/Negligible aspect from {other_planet.upper()} (+1)")
            
            # Malefic aspects (Saturn, Mars)
            if other_planet in ['saturn', 'mars']:
                if aspect_level == 'high':
                    pabathuvam_points += 2
                    pabathuvam_reasons.append(f"High aspect from {other_planet.upper()} (-2)")
                elif aspect_level in ['medium', 'negligible']:
                    pabathuvam_points += 1
                    pabathuvam_reasons.append(f"Medium/Negligible aspect from {other_planet.upper()} (-1)")
        
        # Only apply if planet has conjunction with Moon or is aspected by Moon
        if moon_effect and 'moon' in positions:
            moon_pos = positions['moon']
            moon_degree = moon_pos['degree']
            moon_house = moon_effect['moon_house']
            
            # Check conjunction with Moon
            if planet != 'moon':
                degree_diff = calculate_degree_difference(planet_pos['degree'], moon_degree)
                conj_level = get_conjunction_level(degree_diff)
                has_conjunction = conj_level != 'none'
            
            # Check if Moon aspects this planet
            aspect_level = check_aspect('moon', moon_degree, planet_pos['degree'])
            has_aspect = aspect_level != 'none'
            
            # Only apply Moon position effect if there's conjunction or aspect
            if has_conjunction or has_aspect:
                multiplier = moon_effect['multiplier']
                effect_type = moon_effect['type']
                
                if effect_type == 'pabathuvam' and multiplier == 0:
                    # Less than 0-90: add to pabathuvam and subtract 1
                    pabathuvam_points += 1
                    connection_type = "conjunction" if has_conjunction else "aspect"
                    pabathuvam_reasons.append(f"Moon position effect (0-90° from Sun) via {connection_type} with Moon: Pabathuvam (+1)")
                elif effect_type == 'subathuva':
                    # 90-120 (0.5), 120-160 (1), or 160-180 (2): add to subathuva
                    subathuva_points += multiplier
                    connection_type = "conjunction" if has_conjunction else "aspect"
                    subathuva_reasons.append(f"Moon position effect ({moon_effect['degree_diff']:.1f}° from Sun) via {connection_type} with Moon: Subathuva (+{multiplier})")
        
        # Check if planet is at 90° or 270° from Moon (Moon's Kendra) when Moon is subathuva type
        if moon_effect and moon_effect['type'] == 'subathuva' and 'moon' in positions:
            moon_pos = positions['moon']
            moon_degree = moon_pos['degree']
            planet_degree = planet_pos['degree']
            
            # Calculate degree difference
            degree_diff = calculate_degree_difference(planet_degree, moon_degree)
            
            # Check if planet is at 90° or 270° from moon (with ±5° tolerance)
            # 90° difference means planet is at 90° or 270° from moon
            if abs(degree_diff - 90) <= 5 and planet not in ['rahu', 'ketu']:
                subathuva_points += 1
                subathuva_reasons.append("Present in Moon's Kendra (+1)")
        
        # Special case for 160-180 range: Apply to ALL planets
        if moon_effect and moon_effect.get('special_case') and moon_effect['multiplier'] == 2:
            moon_house = moon_effect['moon_house']
            # Calculate 6th and 8th house from Moon
            moon_6th_house = ((moon_house + 5) % 12) or 12
            moon_8th_house = ((moon_house + 7) % 12) or 12
            moon_7th_house = ((moon_house + 6) % 12) or 12

            # Check if current planet is in 6th or 8th house from Moon
            if planet_pos['house'] == moon_6th_house or planet_pos['house'] == moon_8th_house and planet not in ['rahu', 'ketu', 'sun']:
                subathuva_points += 1
                subathuva_reasons.append(f"Planet in 6th/8th house from Moon (special case): +1")
            
            # Check if planet is joined with or aspected by Jupiter/Venus
            for other_planet in ['jupiter', 'venus']:
                if other_planet not in positions:
                    continue
                other_pos = positions[other_planet]
                
        
        breakdown['subathuva'] = {'value': subathuva_points, 'reason': '; '.join(subathuva_reasons) if subathuva_reasons else 'No benefic influences'}
        breakdown['pabathuvam'] = {'value': -pabathuvam_points, 'reason': '; '.join(pabathuvam_reasons) if pabathuvam_reasons else 'No malefic influences'}
        
        # Check for Exaltation-Debilitation Conjunction first (before applying regular exaltation/debilitation logic)
        has_exalt_debil_conjunction = False
        if planet in PLANET_EXALTATION and planet in PLANET_DEBILITATION:
            exalt_rasi = PLANET_EXALTATION[planet]
            debil_rasi = PLANET_DEBILITATION[planet]
            is_exalted = (planet_pos['rasi'] == exalt_rasi)
            is_debilitated = (planet_pos['rasi'] == debil_rasi)
            
            for other_planet in PLANETS:
                if other_planet == planet or other_planet not in positions:
                    continue
                
                # Special rule: Don't apply for Sun-Saturn conjunction
                if (planet == 'sun' and other_planet == 'saturn') or \
                   (planet == 'saturn' and other_planet == 'sun'):
                    continue
                
                other_pos = positions[other_planet]
                degree_diff = calculate_degree_difference(
                    planet_pos['degree'],
                    other_pos['degree']
                )
                conj_level = get_conjunction_level(degree_diff)
                
                if conj_level == 'none':
                    continue
                
                # Check if other planet is in exaltation or debilitation
                if other_planet in PLANET_EXALTATION and other_planet in PLANET_DEBILITATION:
                    other_exalted = (other_pos['rasi'] == PLANET_EXALTATION[other_planet])
                    other_debilitated = (other_pos['rasi'] == PLANET_DEBILITATION[other_planet])
                    
                    # If this planet is debilitated and other is exalted
                    if is_debilitated and other_exalted:
                        has_exalt_debil_conjunction = True
                        if conj_level in ['very_high', 'high']:
                            breakdown['exalt_debil_conjunction'] = {'value': 2, 'reason': f'Debilitated planet conjuncted with exalted {other_planet.upper()} (high/very high)'}
                        else:
                            breakdown['exalt_debil_conjunction'] = {'value': 1, 'reason': f'Debilitated planet conjuncted with exalted {other_planet.upper()} (medium/less)'}
                    
                    # If this planet is exalted and other is debilitated
                    elif is_exalted and other_debilitated:
                        has_exalt_debil_conjunction = True
                        if conj_level in ['very_high', 'high']:
                            breakdown['exalt_debil_conjunction'] = {'value': -2, 'reason': f'Exalted planet conjuncted with debilitated {other_planet.upper()} (high/very high)'}
                        else:
                            breakdown['exalt_debil_conjunction'] = {'value': -1, 'reason': f'Exalted planet conjuncted with debilitated {other_planet.upper()} (medium/less)'}
        
        # 5. Exaltation and Debilitation (only if no exaltation-debilitation conjunction was found)
        if not has_exalt_debil_conjunction and planet in PLANET_EXALTATION:
            if planet_pos['rasi'] == PLANET_EXALTATION[planet]:
                breakdown['exaltation_debilitation'] = {'value': 2, 'reason': f'Planet is exalted in {planet_pos["rasi"]}'}
            elif planet in PLANET_DEBILITATION and planet_pos['rasi'] == PLANET_DEBILITATION[planet]:
                breakdown['exaltation_debilitation'] = {'value': -2, 'reason': f'Planet is debilitated in {planet_pos["rasi"]}'}
        
        # 5a. Debilitation Cancellation: Check sign lord of debilitation sign
        # If planet is debilitated, check if the sign lord is exalted or in own house
        if planet in PLANET_DEBILITATION and planet_pos['rasi'] == PLANET_DEBILITATION[planet] and not has_exalt_debil_conjunction:
            debil_rasi = PLANET_DEBILITATION[planet]
            
            # Find the sign lord of the debilitation sign
            debil_sign_lord = None
            for lord, houses in PLANET_OWN_HOUSES.items():
                if debil_rasi in houses:
                    debil_sign_lord = lord
                    break
            
            # Check if the sign lord is present in positions and is exalted or in own house
            if debil_sign_lord and debil_sign_lord in positions:
                sign_lord_pos = positions[debil_sign_lord]
                
                # Check if sign lord is exalted (prioritize this as it gives more points)
                if debil_sign_lord in PLANET_EXALTATION and sign_lord_pos['rasi'] == PLANET_EXALTATION[debil_sign_lord]:
                    breakdown['exaltation_debilitation'] = {
                        'value': 2,
                        'reason': f'Planet is debilitated, but sign lord {debil_sign_lord.upper()} is exalted (+2 cancellation)'
                    }
                # Check if sign lord is in own house (only if not exalted)
                elif debil_sign_lord in PLANET_OWN_HOUSES and sign_lord_pos['rasi'] in PLANET_OWN_HOUSES[debil_sign_lord]:
                    breakdown['exaltation_debilitation'] = {
                        'value': 1,
                        'reason': f'Planet is debilitated, but sign lord {debil_sign_lord.upper()} is in own house (+1 cancellation)'
                    }
        
        # 4. Position (own house)
        if planet in PLANET_OWN_HOUSES:
            if planet_pos['rasi'] in PLANET_OWN_HOUSES[planet] and not has_exalt_debil_conjunction:
                breakdown['position'] = {'value': 2, 'reason': f'Planet in its own house - {planet_pos["rasi"]}'}
        
        # 6. Friendship (relationship with sign lord)
        if planet in PLANET_RELATIONSHIPS:
            # Determine sign lord of current rasi
            sign_lord = None
            for lord, houses in PLANET_OWN_HOUSES.items():
                if planet_pos['rasi'] in houses:
                    sign_lord = lord
                    break
            
            if sign_lord:
                if sign_lord in PLANET_RELATIONSHIPS[planet]['friend']:
                    breakdown['friendship'] = {'value': 1, 'reason': f'Sign lord {sign_lord.upper()} is a friend'}
                elif sign_lord in PLANET_RELATIONSHIPS[planet]['enemy']:
                    breakdown['friendship'] = {'value': -1, 'reason': f'Sign lord {sign_lord.upper()} is an enemy'}
                else:
                    breakdown['friendship'] = {'value': 0, 'reason': f'Sign lord {sign_lord.upper()} is neutral'}
        
        # 7. Special Houses
        house = planet_pos['house']
        special_reasons = []
        
        # 1, 4, 7, 10 (Kendras) or 1, 5, 9 (Trikonas)
        if house in [4, 7, 10] and planet not in ['rahu', 'ketu']:
            breakdown['special_houses']['value'] += 1
            special_reasons.append(f"House {house} is a Kendra (Angular house)")
        if house in [5, 9] and planet not in ['rahu', 'ketu']:
            breakdown['special_houses']['value'] += 1
            special_reasons.append(f"House {house} is a Trikona (Trine house)")
        
        if special_reasons:
            breakdown['special_houses']['reason'] = '; '.join(special_reasons)
        else:
            breakdown['special_houses']['reason'] = 'Not in special houses'
        
        # 8. Drik Balam
        drik_balam_reasons = []
        if planet in DRIK_BALAM_LOGIC:
            if DRIK_BALAM_LOGIC[planet]['gain'] == house:
                breakdown['drik_balam']['value'] += 1
                drik_balam_reasons.append(f"Planet in {DRIK_BALAM_LOGIC[planet]['gain']}th house (favorable)")
            elif DRIK_BALAM_LOGIC[planet]['loss'] == house:
                breakdown['drik_balam']['value'] -= 1
                drik_balam_reasons.append(f"Planet in {DRIK_BALAM_LOGIC[planet]['loss']}th house (unfavorable)")
            elif DRIK_BALAM_LOGIC[planet]['gain'] == house + 1 or DRIK_BALAM_LOGIC[planet]['gain'] == house - 1:
                breakdown['drik_balam']['value'] += 0.5
                drik_balam_reasons.append(f"Planet is near to {DRIK_BALAM_LOGIC[planet]['gain']}th house (favorable)")
            elif DRIK_BALAM_LOGIC[planet]['loss'] == house or DRIK_BALAM_LOGIC[planet]['loss'] == house + 1 or DRIK_BALAM_LOGIC[planet]['loss'] == house - 1:
                breakdown['drik_balam']['value'] -= 0.5
                drik_balam_reasons.append(f"Planet is near to {DRIK_BALAM_LOGIC[planet]['loss']}th house (unfavorable)")
                
        if drik_balam_reasons:
            breakdown['drik_balam']['reason'] = '; '.join(drik_balam_reasons)
        else:
            breakdown['drik_balam']['reason'] = 'Not in Drik Balam'
        
        # 9. Planetary Exchange
        # Check if planet is in another planet's house and that planet is in this planet's house
        if planet in PLANET_OWN_HOUSES:
            for other_planet in PLANETS:
                if other_planet == planet or other_planet not in positions:
                    continue
                
                # Check if other planet has own houses (rahu and ketu don't have own houses)
                if other_planet not in PLANET_OWN_HOUSES:
                    continue
                
                other_pos = positions[other_planet]
                
                # Check if this planet is in other planet's house(s)
                this_in_other_house = planet_pos['rasi'] in PLANET_OWN_HOUSES[other_planet]
                
                # Check if other planet is in this planet's house(s)
                other_in_this_house = other_pos['rasi'] in PLANET_OWN_HOUSES[planet]
                
                # If both conditions are true, it's a planetary exchange
                if this_in_other_house and other_in_this_house:
                    breakdown['planetery_exchange'] = {'value': 2, 'reason': f'Planetary exchange with {other_planet.upper()} (mutual house exchange)'}
                    break  # Found exchange, no need to check further
        
        # Don't double count own house and exalted for Mercury
        if planet == 'mercury':
            if breakdown['position'].get('value', 0) == 2 and breakdown['exaltation_debilitation'].get('value', 0) == 2:
                breakdown['exaltation_debilitation'] = {'value': 0, 'reason': 'Mercury: Own house and exaltation not double counted'}
        
        # Ensure all breakdown values are objects
        for key in ['position', 'exaltation_debilitation', 'friendship', 'special_houses', 'exalt_debil_conjunction', 'planetery_exchange', 'combust']:
            if isinstance(breakdown[key], (int, float)):
                breakdown[key] = {'value': breakdown[key], 'reason': 'No specific reason'}
        
        # Calculate final score
        final_score = (
            base_score +
            subathuva_points +
            breakdown['position'].get('value', 0) +
            breakdown['exaltation_debilitation'].get('value', 0) +
            breakdown['friendship'].get('value', 0) +
            breakdown['special_houses'].get('value', 0) +
            breakdown['drik_balam'].get('value', 0) +
            breakdown['exalt_debil_conjunction'].get('value', 0) +
            breakdown['planetery_exchange'].get('value', 0) +
            breakdown['combust'].get('value', 0)
        ) - pabathuvam_points
        
        # Clamp between -5 and 15
        final_score = max(-5, min(15, final_score))
        
        results[planet] = {
            'planet': planet,
            'absolute_degree': round(planet_pos['degree'], 2),
            'rasi': planet_pos['rasi'],
            'house': planet_pos['house'],
            'final_score': round(final_score, 2),
            'breakdown': breakdown
        }
    
    return results

