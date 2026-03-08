from flask import Blueprint, jsonify, request
from calculations import calculate_subathuva_pabathuvam, calculate_house_subathuva_pabathuvam, calculate_professions, calculate_dasha_antardasha, calculate_all_dashas_120_years
from chart_generator import generate_south_indian_chart
from utils.constant import RASI_TO_DEGREE, PLANET_OWN_HOUSES

calculate_bp = Blueprint('calculate', __name__, url_prefix='/api')

@calculate_bp.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'status': 'error'
            }), 400
        
        # Validate required fields
        required_fields = ['ascendant', 'sun', 'moon', 'mars', 'mercury', 
                          'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing field: {field}',
                    'status': 'error'
                }), 400
            
            if not data[field].get('degree') or not data[field].get('house'):
                return jsonify({
                    'error': f'Missing degree or house for: {field}',
                    'status': 'error'
                }), 400
        
        # Perform calculations for planets
        results = calculate_subathuva_pabathuvam(data)
        
        # Get positions for house calculations (reuse from planet calculations)
        # We need to reconstruct positions from results
        positions = {}
        ascendant_rasi = data.get('ascendant', {}).get('house', '')
        
        if ascendant_rasi:
            from calculations import rasi_to_absolute_degree, get_house_number
            asc_degree = rasi_to_absolute_degree(
                ascendant_rasi,
                float(data.get('ascendant', {}).get('degree', 0))
            )
            positions['ascendant'] = {
                'degree': asc_degree,
                'rasi': ascendant_rasi,
                'house': 1
            }
        
        for planet in ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']:
            if planet in results:
                result = results[planet]
                positions[planet] = {
                    'degree': result['absolute_degree'],
                    'rasi': result['rasi'],
                    'house': result['house']
                }
        
        # Calculate house Subathuva/Pabathuvam
        house_results = calculate_house_subathuva_pabathuvam(data, results, positions)
        
        # Format planet results as table
        table_data = []
        for planet, result in results.items():
            breakdown = result['breakdown']
            
            # Helper function to extract value and reason
            def get_value_reason(key):
                item = breakdown.get(key, {'value': 0, 'reason': ''})
                if isinstance(item, dict):
                    return item.get('value', 0), item.get('reason', '')
                return item, ''
            
            base_val, base_reason = get_value_reason('base')
            suba_val, suba_reason = get_value_reason('subathuva')
            paba_val, paba_reason = get_value_reason('pabathuvam')
            pos_val, pos_reason = get_value_reason('position')
            exalt_val, exalt_reason = get_value_reason('exaltation_debilitation')
            friend_val, friend_reason = get_value_reason('friendship')
            special_val, special_reason = get_value_reason('special_houses')
            # mutual_val, mutual_reason = get_value_reason('mutual_aspect')
            exalt_debil_val, exalt_debil_reason = get_value_reason('exalt_debil_conjunction')
            combust_val, combust_reason = get_value_reason('combust')
            drik_balam_val, drik_balam_reason = get_value_reason('drik_balam')
            planetery_exchange_val, planetery_exchange_reason = get_value_reason('planetery_exchange')

            table_data.append({
                'planet': planet.upper(),
                'absolute_degree': result['absolute_degree'],
                'rasi': result['rasi'],
                'house': result['house'],
                'base': {'value': base_val, 'reason': base_reason},
                'subathuva': {'value': suba_val, 'reason': suba_reason},
                'pabathuvam': {'value': paba_val, 'reason': paba_reason},
                'position_bonus': {'value': pos_val, 'reason': pos_reason},
                'exaltation_debilitation': {'value': exalt_val, 'reason': exalt_reason},
                'friendship': {'value': friend_val, 'reason': friend_reason},
                'special_houses': {'value': special_val, 'reason': special_reason},
                # 'mutual_aspect': {'value': mutual_val, 'reason': mutual_reason},
                'drik_balam': {'value': drik_balam_val, 'reason': drik_balam_reason},
                'exalt_debil_conjunction': {'value': exalt_debil_val, 'reason': exalt_debil_reason},
                'planetery_exchange': {'value': planetery_exchange_val, 'reason': planetery_exchange_reason},
                'combust': {'value': combust_val, 'reason': combust_reason},
                'final_score': result['final_score']
            })
        
        # Calculate house-rasi mapping based on ascendant
        ascendant_rasi = data.get('ascendant', {}).get('house', '')
        house_rasi_map = {}
        if ascendant_rasi:
            rasi_list = list(RASI_TO_DEGREE.keys())
            asc_index = rasi_list.index(ascendant_rasi)
            for i in range(1, 13):
                rasi_index = (asc_index + i - 1) % 12
                house_rasi_map[i] = rasi_list[rasi_index]
        
        # Create a map of planets to houses they own based on ascendant
        planet_owned_houses = {}
        if ascendant_rasi:
            for planet, owned_rasi_list in PLANET_OWN_HOUSES.items():
                owned_houses = []
                for rasi in owned_rasi_list:
                    # Find which house number corresponds to this rasi
                    for house_num in range(1, 13):
                        if house_rasi_map.get(house_num) == rasi:
                            owned_houses.append(house_num)
                planet_owned_houses[planet] = owned_houses
        
        # Format house results as table
        house_table_data = []
        for house_num in range(1, 13):
            if house_num in house_results:
                house_result = house_results[house_num]
                breakdown = house_result['breakdown']
                
                # Helper function to extract value and reason
                def get_value_reason(key):
                    item = breakdown.get(key, {'value': 0, 'reason': ''})
                    if isinstance(item, dict):
                        return item.get('value', 0), item.get('reason', '')
                    return item, ''
                
                base_val, base_reason = get_value_reason('base')
                suba_val, suba_reason = get_value_reason('subathuva')
                paba_val, paba_reason = get_value_reason('pabathuvam')
                planets_val, planets_reason = get_value_reason('planets_in_house')
                benefic_val, benefic_reason = get_value_reason('benefic_aspects')
                malefic_val, malefic_reason = get_value_reason('malefic_aspects')
                
                # Build planets_list with owned houses information
                planets_list = []
                for planet in house_result['planets_in_house']:
                    planet_lower = planet.lower()
                    owned_houses = planet_owned_houses.get(planet_lower, [])
                    planets_list.append({
                        'name': planet.upper(),
                        'owned_houses': owned_houses
                    })
                
                house_table_data.append({
                    'house': house_num,
                    'rasi': house_result['rasi'],
                    'base': {'value': base_val, 'reason': base_reason},
                    'subathuva': {'value': suba_val, 'reason': suba_reason},
                    'pabathuvam': {'value': paba_val, 'reason': paba_reason},
                    'planets_in_house': {'value': planets_val, 'reason': planets_reason},
                    'benefic_aspects': {'value': benefic_val, 'reason': benefic_reason},
                    'malefic_aspects': {'value': malefic_val, 'reason': malefic_reason},
                    'final_score': house_result['final_score'],
                    'planets_list': planets_list
                })
        
        # Generate South Indian style chart HTML
        chart_html = generate_south_indian_chart(data, results)
        
        
        # Calculate professions data
        profession_data = calculate_professions(data, results, positions, house_results)
        
        # Generate profession prediction using AI
        # profession_json = {
        #     "planets": [],
        #     "professions": []
        # }
        # if profession_data:
        #     try:
        #         # Import here to avoid circular dependency
        #         from blueprints.ai import generate_profession_prediction
        #         profession_result = generate_profession_prediction(profession_data)
        #         # Ensure it's a dict (the function should return a dict)
        #         if isinstance(profession_result, dict):
        #             profession_json = profession_result
        #         else:
        #             # Fallback if it's not a dict
        #             profession_json = {
        #                 "planets": [],
        #                 "professions": [],
        #                 "error": "Invalid response format"
        #             }
        #     except Exception as e:
        #         profession_json = {
        #             "planets": [],
        #             "professions": [],
        #             "error": str(e)
        #         }
        
        # Default empty profession data when prediction is commented out
        profession_json = {
            "planets": [],
            "professions": []
        }
        
        # Helper functions for relationship and marriage data
        def get_house(num):
            return next((h for h in house_table_data if h['house'] == num), None)

        def get_house_lord(num):
            rasi = house_rasi_map.get(num, '')
            lord = None
            for planet, owned_rasi_list in PLANET_OWN_HOUSES.items():
                if rasi in owned_rasi_list:
                    lord = planet
                    break
            score = next((p for p in table_data if p['planet'].lower() == lord), None) if lord else None
            return {'planet': lord, 'score': score}

        def get_planet(name):
            return next((p for p in table_data if p['planet'] == name.upper()), None)

        def get_rasi_house(rasi):
            return next((h for h in house_table_data if h['rasi'] == rasi), None)

        # Build marriage data
        rasi_list = list(RASI_TO_DEGREE.keys())
        moon_rasi = positions.get('moon', {}).get('rasi', '')

        def get_house_by_rasi(rasi):
            return next((h for h in house_table_data if h['rasi'] == rasi), None)

        def rasi_offset(base_rasi, offset):
            if not base_rasi or base_rasi not in rasi_list:
                return None
            return rasi_list[(rasi_list.index(base_rasi) + offset) % 12]

        marriage = {
            'from_lagna': {
                'second_house': get_house(2),
                'seventh_house': get_house(7),
                'eighth_house': get_house(8)
            },
            'from_moon': {
                'second_house': get_house_by_rasi(rasi_offset(moon_rasi, 1)),
                'seventh_house': get_house_by_rasi(rasi_offset(moon_rasi, 6)),
                'eighth_house': get_house_by_rasi(rasi_offset(moon_rasi, 7))
            },
            'key_indicators': {
                'seventh_house': get_house(7),
                'seventh_house_lord': get_house_lord(7),
                'venus': get_planet('venus')
            }
        }

        relationship = {
            'father': {
                'ninth_house': get_house(9),
                'ninth_house_lord': get_house_lord(9),
                'sun': get_planet('sun'),
                'simha_house': get_rasi_house('simha')
            },
            'mother': {
                'fourth_house': get_house(4),
                'fourth_house_lord': get_house_lord(4),
                'moon': get_planet('moon'),
                'kadagam_house': get_rasi_house('karka')
            },
            'younger_brother': {
                'third_house': get_house(3),
                'third_house_lord': get_house_lord(3),
                'mars': get_planet('mars'),
                'mesha_house': get_rasi_house('mesha'),
                'vrishchika_house': get_rasi_house('vrishchika')
            },
            'spouse': {
                'seventh_house': get_house(7),
                'seventh_house_lord': get_house_lord(7),
                'venus': get_planet('venus'),
                'vrishabha_house': get_rasi_house('vrishabha'),
                'thulam_house': get_rasi_house('tula')
            },
            'children': {
                'fifth_house': get_house(5),
                'fifth_house_lord': get_house_lord(5),
                'jupiter': get_planet('jupiter'),
                'meena_house': get_rasi_house('meena'),
                'dhanu_house': get_rasi_house('dhanu')
            },
            'elder_brother': {
                'eleventh_house': get_house(11),
                'eleventh_house_lord': get_house_lord(11),
                'mars': get_planet('mars'),
                'mesha_house': get_rasi_house('mesha'),
                'vrishchika_house': get_rasi_house('vrishchika')
            },
            'elder_sister': {
                'eleventh_house': get_house(11),
                'eleventh_house_lord': get_house_lord(11),
                'venus': get_planet('venus'),
                'vrishabha_house': get_rasi_house('vrishabha'),
                'thulam_house': get_rasi_house('tula')
            },
            'younger_sister': {
                'third_house': get_house(3),
                'third_house_lord': get_house_lord(3),
                'venus': get_planet('venus'),
                'vrishabha_house': get_rasi_house('vrishabha'),
                'thulam_house': get_rasi_house('tula')
            }
        }

        response_data = {
            'status': 'success',
            'results': table_data,
            'house_results': house_table_data,
            'chart_html': chart_html,
            'prediction': {
                'profession': profession_json
            },
            'relationship': relationship,
            'marriage': marriage,
            'summary': {
                'total_planets': len(table_data),
                'average_score': round(sum(r['final_score'] for r in table_data) / len(table_data), 2) if table_data else 0,
                'total_houses': len(house_table_data),
                'average_house_score': round(sum(r['final_score'] for r in house_table_data) / len(house_table_data), 2) if house_table_data else 0
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@calculate_bp.route('/dasha-info', methods=['POST'])
def dasha_info():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'status': 'error'
            }), 400
        
        moon_rasi = data.get('moon', {}).get('house', '')
        moon_degree = data.get('moon', {}).get('degree', '0')
        birth_date = data.get('birth_date')  # Optional birth date (YYYY-MM-DD format)
        
        if not moon_rasi or not moon_degree:
            return jsonify({
                'error': 'Moon rasi and degree are required',
                'status': 'error'
            }), 400
        
        try:
            moon_degree_float = float(moon_degree)
            dasha_info = calculate_dasha_antardasha(moon_rasi, moon_degree_float, birth_date)
            
            if dasha_info:
                return jsonify({
                    'status': 'success',
                    'dasha': dasha_info
                }), 200
            else:
                return jsonify({
                    'error': 'Failed to calculate dasha information',
                    'status': 'error'
                }), 500
        except (ValueError, TypeError) as e:
            return jsonify({
                'error': f'Invalid input: {str(e)}',
                'status': 'error'
            }), 400
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@calculate_bp.route('/all-dashas', methods=['POST'])
def all_dashas():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'status': 'error'
            }), 400
        
        moon_rasi = data.get('moon', {}).get('house', '')
        moon_degree = data.get('moon', {}).get('degree', '0')
        birth_date = data.get('birth_date')  # Required birth date (YYYY-MM-DD format)
        
        if not moon_rasi or not moon_degree:
            return jsonify({
                'error': 'Moon rasi and degree are required',
                'status': 'error'
            }), 400
        
        if not birth_date:
            return jsonify({
                'error': 'Birth date is required',
                'status': 'error'
            }), 400
        
        try:
            moon_degree_float = float(moon_degree)
            all_dashas_info = calculate_all_dashas_120_years(moon_rasi, moon_degree_float, birth_date)
            
            if all_dashas_info:
                return jsonify({
                    'status': 'success',
                    'data': all_dashas_info
                }), 200
            else:
                return jsonify({
                    'error': 'Failed to calculate all dashas',
                    'status': 'error'
                }), 500
        except (ValueError, TypeError) as e:
            return jsonify({
                'error': f'Invalid input: {str(e)}',
                'status': 'error'
            }), 400
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500