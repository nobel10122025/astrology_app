"""
Dasha and Antardasha calculation functions
"""

from utils.constant import NAKSHATRAS, DASHA_PERIODS, DASHA_SEQUENCE, TAMIL_YEAR
from utils.calculations.utils import rasi_to_absolute_degree, normalize_degree
from datetime import datetime, timedelta


def get_nakshatra_from_degree(degree):
    """
    Get nakshatra information from absolute degree (0-360)
    Returns: (nakshatra_name, dasha_lord, degree_in_nakshatra)
    """
    degree = normalize_degree(degree)
    
    # Find which nakshatra the degree falls into
    for i, (start_degree, name, dasha_lord) in enumerate(NAKSHATRAS):
        # Calculate end degree (next nakshatra start or 360)
        if i < len(NAKSHATRAS) - 1:
            end_degree = NAKSHATRAS[i + 1][0]
        else:
            end_degree = 360
        
        if start_degree <= degree < end_degree:
            degree_in_nakshatra = degree - start_degree
            return name, dasha_lord, degree_in_nakshatra
    
    # Handle edge case (degree exactly at 360 or 0)
    return NAKSHATRAS[0][1], NAKSHATRAS[0][2], 0


def calculate_dasha_remaining(moon_degree):
    """
    Calculate remaining dasha period from Moon's degree
    Returns: dictionary with dasha information
    """
    nakshatra_name, dasha_lord, degree_in_nakshatra = get_nakshatra_from_degree(moon_degree)
    
    # Each nakshatra spans 13.333 degrees
    nakshatra_span = 13.333
    
    # Calculate elapsed portion of nakshatra (0 to 1)
    elapsed_portion = degree_in_nakshatra / nakshatra_span
    
    # Total dasha period for this lord
    total_dasha_years = DASHA_PERIODS[dasha_lord]
    
    # Calculate elapsed time in dasha
    elapsed_years = total_dasha_years * elapsed_portion
    
    # Calculate remaining time
    remaining_years = total_dasha_years - elapsed_years
    
    # Convert to days
    remaining_days = remaining_years * TAMIL_YEAR
    
    return {
        'current_dasha_lord': dasha_lord,
        'nakshatra': nakshatra_name,
        'elapsed_years': elapsed_years,
        'remaining_years': remaining_years,
        'remaining_days': remaining_days,
        'elapsed_portion': elapsed_portion,
        'total_dasha_years': total_dasha_years
    }


def calculate_antardashas(current_dasha_lord, remaining_years):
    """
    Calculate all antardashas (sub-periods) for the current dasha
    Returns: List of antardashas with their durations
    """
    total_dasha_years = DASHA_PERIODS[current_dasha_lord]
    
    # Find current dasha position in sequence
    dasha_index = DASHA_SEQUENCE.index(current_dasha_lord)
    
    antardashas = []
    cumulative_days = 0
    
    # Calculate antardashas in sequence starting from current dasha
    for i in range(9):
        antardasha_lord = DASHA_SEQUENCE[(dasha_index + i) % 9]
        antardasha_period_years = (DASHA_PERIODS[antardasha_lord] / 120) * total_dasha_years
        antardasha_period_days = antardasha_period_years * TAMIL_YEAR
        
        antardashas.append({
            'lord': antardasha_lord,
            'period_years': antardasha_period_years,
            'period_days': antardasha_period_days,
            'start_day': cumulative_days,
            'end_day': cumulative_days + antardasha_period_days
        })
        
        cumulative_days += antardasha_period_days
    
    return antardashas


def calculate_pratyantardashas(antardasha_lord, antardasha_period_years):
    """
    Calculate all pratyantardashas (sub-sub-periods) for a given antardasha
    Args:
        antardasha_lord: The lord of the antardasha
        antardasha_period_years: Total period of the antardasha in years
    Returns: List of pratyantardashas with their durations
    """
    # Find antardasha lord position in sequence
    antardasha_index = DASHA_SEQUENCE.index(antardasha_lord)
    
    pratyantardashas = []
    cumulative_days = 0
    
    # Calculate pratyantardashas in sequence starting from antardasha lord
    for i in range(9):
        pratyantar_lord = DASHA_SEQUENCE[(antardasha_index + i) % 9]
        pratyantar_period_years = (DASHA_PERIODS[pratyantar_lord] / 120) * antardasha_period_years
        pratyantar_period_days = pratyantar_period_years * TAMIL_YEAR
        
        pratyantardashas.append({
            'lord': pratyantar_lord,
            'period_years': pratyantar_period_years,
            'period_days': pratyantar_period_days,
            'start_day': cumulative_days,
            'end_day': cumulative_days + pratyantar_period_days
        })
        
        cumulative_days += pratyantar_period_days
    
    return pratyantardashas


def calculate_dasha_antardasha(moon_rasi, moon_degree_in_sign, birth_date_str=None):
    """
    Main function to calculate current dasha and antardasha based on age and progression
    Args:
        moon_rasi: Moon's rasi (sign)
        moon_degree_in_sign: Moon's degree within the sign (0-30)
        birth_date_str: Birth date as string (YYYY-MM-DD) - REQUIRED for current dasha calculation
    Returns:
        Dictionary with current dasha and antardasha information
    """
    # Convert to absolute degree
    moon_abs_degree = rasi_to_absolute_degree(moon_rasi, moon_degree_in_sign)
    
    if moon_abs_degree is None:
        return None
    
    # Get birth dasha information (starting dasha from Moon's nakshatra)
    birth_dasha_info = calculate_dasha_remaining(moon_abs_degree)
    birth_dasha_lord = birth_dasha_info['current_dasha_lord']
    birth_nakshatra = birth_dasha_info['nakshatra']
    
    # Calculate elapsed portion of birth dasha at birth
    elapsed_portion_at_birth = birth_dasha_info['elapsed_portion']
    birth_dasha_total_days = birth_dasha_info['total_dasha_years'] * TAMIL_YEAR
    elapsed_days_at_birth = elapsed_portion_at_birth * birth_dasha_total_days
    remaining_days_at_birth = birth_dasha_total_days - elapsed_days_at_birth
    
    # If no birth date, return birth dasha info only
    if not birth_date_str:
        return {
            'dasha': {
                'lord': birth_dasha_lord,
                'nakshatra': birth_nakshatra,
                'remaining_years': round(birth_dasha_info['remaining_years'], 4),
                'remaining_days': round(birth_dasha_info['remaining_days'], 2),
                'end_date': None,
                'total_period_years': birth_dasha_info['total_dasha_years'],
                'is_birth_dasha': True
            },
            'current_antardasha': None,
            'all_antardashas': []
        }
    
    try:
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')
        current_date = datetime.now()
        
        # Calculate total days since birth
        total_days_since_birth = (current_date - birth_date).days
        
        # Start from birth dasha
        current_dasha_lord = birth_dasha_lord
        days_remaining_in_current_dasha = remaining_days_at_birth
        
        # Progress through dashas to find current dasha
        # Start from the birth dasha index
        dasha_index = DASHA_SEQUENCE.index(birth_dasha_lord)
        
        # Calculate how many days we need to account for
        days_to_account_for = total_days_since_birth
        
        # Progress through dashas
        while days_to_account_for > 0:
            if days_to_account_for <= days_remaining_in_current_dasha:
                # We're still in the current dasha
                days_remaining_in_current_dasha -= days_to_account_for
                break
            else:
                # Move to next dasha
                days_to_account_for -= days_remaining_in_current_dasha
                
                # Move to next dasha in sequence
                dasha_index = (dasha_index + 1) % len(DASHA_SEQUENCE)
                current_dasha_lord = DASHA_SEQUENCE[dasha_index]
                days_remaining_in_current_dasha = DASHA_PERIODS[current_dasha_lord] * TAMIL_YEAR
        
        # Calculate current dasha information
        current_dasha_total_years = DASHA_PERIODS[current_dasha_lord]
        current_dasha_remaining_years = days_remaining_in_current_dasha / TAMIL_YEAR
        current_dasha_elapsed_years = current_dasha_total_years - current_dasha_remaining_years
        
        # Calculate dasha start and end dates
        # Find when current dasha started
        days_elapsed_in_current_dasha = current_dasha_elapsed_years * TAMIL_YEAR
        current_dasha_start_date = current_date - timedelta(days=days_elapsed_in_current_dasha)
        current_dasha_end_date = current_dasha_start_date + timedelta(days=current_dasha_total_years * TAMIL_YEAR)
        
        # Calculate antardashas for current dasha
        antardashas = calculate_antardashas(current_dasha_lord, current_dasha_remaining_years)
        
        # Find current antardasha
        current_antardasha = None
        for antardasha in antardashas:
            # Calculate days elapsed in current dasha
            days_elapsed = current_dasha_elapsed_years * TAMIL_YEAR
            if antardasha['start_day'] <= days_elapsed < antardasha['end_day']:
                current_antardasha = antardasha
                # Calculate remaining days in current antardasha
                remaining_days_in_antardasha = antardasha['end_day'] - days_elapsed
                current_antardasha['remaining_days'] = remaining_days_in_antardasha
                break
        
        # Calculate antardasha start and end dates
        antardasha_start_date = None
        antardasha_end_date = None
        if current_antardasha:
            antardasha_start_date = current_dasha_start_date + timedelta(days=current_antardasha['start_day'])
            antardasha_end_date = current_dasha_start_date + timedelta(days=current_antardasha['end_day'])
        
        # Calculate pratyantar_dashas for current antardasha
        current_pratyantardashas = []
        if current_antardasha:
            current_pratyantardashas = calculate_pratyantardashas(
                current_antardasha['lord'],
                current_antardasha['period_years']
            )
            # Add start_date and end_date for each pratyantar_dasha
            for pratyantar in current_pratyantardashas:
                pratyantar['start_date'] = (antardasha_start_date + timedelta(days=pratyantar['start_day'])).strftime('%Y-%m-%d')
                pratyantar['end_date'] = (antardasha_start_date + timedelta(days=pratyantar['end_day'])).strftime('%Y-%m-%d')
        
        # Calculate pratyantar_dashas for all antardashas
        all_antardashas_with_pratyantar = []
        for ad in antardashas:
            antardasha_start = current_dasha_start_date + timedelta(days=ad['start_day'])
            pratyantardashas = calculate_pratyantardashas(ad['lord'], ad['period_years'])
            # Add start_date and end_date for each pratyantar_dasha
            for pratyantar in pratyantardashas:
                pratyantar['start_date'] = (antardasha_start + timedelta(days=pratyantar['start_day'])).strftime('%Y-%m-%d')
                pratyantar['end_date'] = (antardasha_start + timedelta(days=pratyantar['end_day'])).strftime('%Y-%m-%d')
            
            all_antardashas_with_pratyantar.append({
                'lord': ad['lord'],
                'period_years': round(ad['period_years'], 4),
                'period_days': round(ad['period_days'], 2),
                'start_date': antardasha_start.strftime('%Y-%m-%d'),
                'end_date': (current_dasha_start_date + timedelta(days=ad['end_day'])).strftime('%Y-%m-%d'),
                'pratyantardashas': [
                    {
                        'lord': p['lord'],
                        'period_years': round(p['period_years'], 4),
                        'period_days': round(p['period_days'], 2),
                        'start_date': p['start_date'],
                        'end_date': p['end_date']
                    }
                    for p in pratyantardashas
                ]
            })
        
        return {
            'dasha': {
                'lord': current_dasha_lord,
                'nakshatra': birth_nakshatra,  # Keep birth nakshatra for reference
                'birth_dasha_lord': birth_dasha_lord,  # Show which dasha started at birth
                'remaining_years': round(current_dasha_remaining_years, 4),
                'remaining_days': round(days_remaining_in_current_dasha, 2),
                'elapsed_years': round(current_dasha_elapsed_years, 4),
                'start_date': current_dasha_start_date.strftime('%Y-%m-%d'),
                'end_date': current_dasha_end_date.strftime('%Y-%m-%d'),
                'total_period_years': current_dasha_total_years,
                'is_birth_dasha': (current_dasha_lord == birth_dasha_lord)
            },
            'current_antardasha': {
                'lord': current_antardasha['lord'] if current_antardasha else None,
                'period_years': round(current_antardasha['period_years'], 4) if current_antardasha else None,
                'period_days': round(current_antardasha['period_days'], 2) if current_antardasha else None,
                'remaining_days': round(current_antardasha['remaining_days'], 2) if current_antardasha and 'remaining_days' in current_antardasha else None,
                'start_date': antardasha_start_date.strftime('%Y-%m-%d') if antardasha_start_date else None,
                'end_date': antardasha_end_date.strftime('%Y-%m-%d') if antardasha_end_date else None,
                'pratyantardashas': [
                    {
                        'lord': p['lord'],
                        'period_years': round(p['period_years'], 4),
                        'period_days': round(p['period_days'], 2),
                        'start_date': p['start_date'],
                        'end_date': p['end_date']
                    }
                    for p in current_pratyantardashas
                ] if current_antardasha else []
            } if current_antardasha else None,
            'all_antardashas': all_antardashas_with_pratyantar
        }
        
    except (ValueError, TypeError) as e:
        # If date parsing fails, return birth dasha info only
        return {
            'dasha': {
                'lord': birth_dasha_lord,
                'nakshatra': birth_nakshatra,
                'remaining_years': round(birth_dasha_info['remaining_years'], 4),
                'remaining_days': round(birth_dasha_info['remaining_days'], 2),
                'end_date': None,
                'total_period_years': birth_dasha_info['total_dasha_years'],
                'is_birth_dasha': True,
                'error': f'Invalid birth date format: {str(e)}'
            },
            'current_antardasha': None,
            'all_antardashas': []
        }


def calculate_all_dashas_120_years(moon_rasi, moon_degree_in_sign, birth_date_str):
    """
    Calculate all dashas for 120 years (complete Vimshottari Dasha cycle)
    Args:
        moon_rasi: Moon's rasi (sign)
        moon_degree_in_sign: Moon's degree within the sign (0-30)
        birth_date_str: Birth date as string (YYYY-MM-DD) - REQUIRED
    Returns:
        Dictionary with all dashas, antardashas, and pratyantardashas for 120 years
    """
    # Convert to absolute degree
    moon_abs_degree = rasi_to_absolute_degree(moon_rasi, moon_degree_in_sign)
    
    if moon_abs_degree is None:
        return None
    
    if not birth_date_str:
        return None
    
    try:
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')
        
        # Get birth dasha information (starting dasha from Moon's nakshatra)
        birth_dasha_info = calculate_dasha_remaining(moon_abs_degree)
        birth_dasha_lord = birth_dasha_info['current_dasha_lord']
        birth_nakshatra = birth_dasha_info['nakshatra']
        
        # Calculate elapsed portion of birth dasha at birth
        elapsed_portion_at_birth = birth_dasha_info['elapsed_portion']
        birth_dasha_total_days = birth_dasha_info['total_dasha_years'] * TAMIL_YEAR
        elapsed_days_at_birth = elapsed_portion_at_birth * birth_dasha_total_days
        remaining_days_at_birth = birth_dasha_total_days - elapsed_days_at_birth
        
        # Find starting dasha index
        dasha_index = DASHA_SEQUENCE.index(birth_dasha_lord)
        
        # Calculate all 9 dashas (120 years total)
        all_dashas = []
        current_date = birth_date
        
        # Process all 9 dashas
        for dasha_cycle in range(9):
            current_dasha_lord = DASHA_SEQUENCE[(dasha_index + dasha_cycle) % 9]
            total_dasha_years = DASHA_PERIODS[current_dasha_lord]
            total_dasha_days = total_dasha_years * TAMIL_YEAR
            
            # For the first dasha, use remaining days; for others, use full period
            if dasha_cycle == 0:
                dasha_start_date = birth_date
                dasha_period_days = remaining_days_at_birth
            else:
                dasha_start_date = current_date
                dasha_period_days = total_dasha_days
            
            dasha_end_date = dasha_start_date + timedelta(days=dasha_period_days)
            
            # Calculate all antardashas for this dasha
            # Start from the beginning of the dasha period
            dasha_actual_start = dasha_start_date - timedelta(days=elapsed_days_at_birth) if dasha_cycle == 0 else dasha_start_date
            antardashas = []
            antardasha_start_date = dasha_actual_start
            
            # Find antardasha starting index (starts from current dasha lord)
            antardasha_start_index = DASHA_SEQUENCE.index(current_dasha_lord)
            
            # Calculate which antardasha we're currently in (for first dasha only)
            current_antardasha_index = 0
            elapsed_in_current_antardasha = 0
            if dasha_cycle == 0:
                cumulative = 0
                for i in range(9):
                    ad_lord = DASHA_SEQUENCE[(antardasha_start_index + i) % 9]
                    ad_period_days = (DASHA_PERIODS[ad_lord] / 120) * total_dasha_years * TAMIL_YEAR
                    if cumulative <= elapsed_days_at_birth < cumulative + ad_period_days:
                        current_antardasha_index = i
                        elapsed_in_current_antardasha = elapsed_days_at_birth - cumulative
                        break
                    cumulative += ad_period_days
            
            for i in range(9):
                antardasha_lord = DASHA_SEQUENCE[(antardasha_start_index + i) % 9]
                antardasha_period_years = (DASHA_PERIODS[antardasha_lord] / 120) * total_dasha_years
                antardasha_period_days = antardasha_period_years * TAMIL_YEAR
                
                # Calculate antardasha dates
                if dasha_cycle == 0 and i == current_antardasha_index:
                    # This is the current antardasha - start from birth date
                    antardasha_start_date = birth_date
                    remaining_days = antardasha_period_days - elapsed_in_current_antardasha
                    antardasha_end_date = antardasha_start_date + timedelta(days=remaining_days)
                else:
                    antardasha_end_date = antardasha_start_date + timedelta(days=antardasha_period_days)
                
                # Calculate all pratyantardashas for this antardasha
                pratyantardashas = []
                pratyantar_start_date = antardasha_start_date
                
                # Find pratyantar starting index (starts from antardasha lord)
                pratyantar_start_index = DASHA_SEQUENCE.index(antardasha_lord)
                
                # Calculate which pratyantar we're currently in (for first antardasha of first dasha only)
                current_pratyantar_index = 0
                elapsed_in_current_pratyantar = 0
                if dasha_cycle == 0 and i == current_antardasha_index:
                    cumulative = 0
                    for j in range(9):
                        pt_lord = DASHA_SEQUENCE[(pratyantar_start_index + j) % 9]
                        pt_period_days = (DASHA_PERIODS[pt_lord] / 120) * antardasha_period_years * TAMIL_YEAR
                        if cumulative <= elapsed_in_current_antardasha < cumulative + pt_period_days:
                            current_pratyantar_index = j
                            elapsed_in_current_pratyantar = elapsed_in_current_antardasha - cumulative
                            break
                        cumulative += pt_period_days
                
                for j in range(9):
                    pratyantar_lord = DASHA_SEQUENCE[(pratyantar_start_index + j) % 9]
                    pratyantar_period_years = (DASHA_PERIODS[pratyantar_lord] / 120) * antardasha_period_years
                    pratyantar_period_days = pratyantar_period_years * TAMIL_YEAR
                    
                    # Calculate pratyantar dates
                    if dasha_cycle == 0 and i == current_antardasha_index and j == current_pratyantar_index:
                        # This is the current pratyantar - start from birth date
                        pratyantar_start_date = birth_date
                        remaining_days = pratyantar_period_days - elapsed_in_current_pratyantar
                        pratyantar_end_date = pratyantar_start_date + timedelta(days=remaining_days)
                    else:
                        pratyantar_end_date = pratyantar_start_date + timedelta(days=pratyantar_period_days)
                    
                    pratyantardashas.append({
                        'lord': pratyantar_lord,
                        'period_years': round(pratyantar_period_years, 4),
                        'period_days': round(pratyantar_period_days, 2),
                        'start_date': pratyantar_start_date.strftime('%Y-%m-%d'),
                        'end_date': pratyantar_end_date.strftime('%Y-%m-%d')
                    })
                    
                    pratyantar_start_date = pratyantar_end_date
                
                antardashas.append({
                    'lord': antardasha_lord,
                    'period_years': round(antardasha_period_years, 4),
                    'period_days': round(antardasha_period_days, 2),
                    'start_date': antardasha_start_date.strftime('%Y-%m-%d'),
                    'end_date': antardasha_end_date.strftime('%Y-%m-%d'),
                    'pratyantardashas': pratyantardashas
                })
                
                antardasha_start_date = antardasha_end_date
            
            all_dashas.append({
                'lord': current_dasha_lord,
                'period_years': round(total_dasha_years, 4),
                'period_days': round(dasha_period_days, 2),
                'start_date': dasha_start_date.strftime('%Y-%m-%d'),
                'end_date': dasha_end_date.strftime('%Y-%m-%d'),
                'antardashas': antardashas
            })
            
            current_date = dasha_end_date
        
        return {
            'birth_nakshatra': birth_nakshatra,
            'birth_dasha_lord': birth_dasha_lord,
            'birth_date': birth_date_str,
            'dashas': all_dashas
        }
        
    except (ValueError, TypeError) as e:
        return None

