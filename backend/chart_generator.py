"""
South Indian Style Rasi Chart Generator
"""

RASI_NAMES = {
    'mesha': 'Mesha',
    'vrishabha': 'Vrishabha',
    'mithuna': 'Mithuna',
    'karka': 'Karka',
    'simha': 'Simha',
    'kanya': 'Kanya',
    'tula': 'Tula',
    'vrishchika': 'Vrishchika',
    'dhanu': 'Dhanu',
    'makara': 'Makara',
    'kumbha': 'Kumbha',
    'meena': 'Meena'
}

PLANET_SYMBOLS = {
    'sun': '☉',
    'moon': '☽',
    'mars': '♂',
    'mercury': '☿',
    'jupiter': '♃',
    'venus': '♀',
    'saturn': '♄',
    'rahu': '☊',
    'ketu': '☋',
    'ascendant': 'Asc'
}

PLANET_NAMES = {
    'sun': 'Su',
    'moon': 'Mo',
    'mars': 'Ma',
    'mercury': 'Me',
    'jupiter': 'Ju',
    'venus': 'Ve',
    'saturn': 'Sa',
    'rahu': 'Ra',
    'ketu': 'Ke',
    'ascendant': 'Asc'
}


def generate_south_indian_chart(data, results):
    """
    Generate South Indian style Rasi chart HTML
    Layout: South Indian style with house 1 at bottom-left
    """
    # Get all positions
    positions = {}
    ascendant_rasi = data.get('ascendant', {}).get('house', '')
    
    # Process ascendant
    if ascendant_rasi:
        asc_degree = float(data.get('ascendant', {}).get('degree', 0))
        positions['ascendant'] = {
            'rasi': ascendant_rasi,
            'house': 1,
            'degree': asc_degree
        }
    
    # Process planets
    planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
    for planet in planets:
        planet_data = data.get(planet, {})
        if planet_data.get('house') and planet_data.get('degree'):
            positions[planet] = {
                'rasi': planet_data['house'],
                'house': results.get(planet, {}).get('house', 0),
                'degree': float(planet_data['degree'])
            }
    
    # South Indian layout: House 1 at bottom-left, going counter-clockwise
    # Layout:
    # [4]  [3]  [2]
    # [5]  [12] [11]
    # [1]  [6]  [7]
    # [10] [9]  [8]
    
    # Actually, standard South Indian is 3x3:
    # Top row: 4, 3, 2
    # Middle row: 5, 12, 11
    # Bottom row: 1, 6, 7
    # And then below: 10, 9, 8 (but that's 4 rows)
    
    # Let me use a 3x3 grid with houses arranged:
    # [4]  [3]  [2]
    # [5]  [12] [11]
    # [1]  [6]  [7]
    # And houses 8, 9, 10 can be shown separately or in a different layout
    
    # Standard South Indian layout - 4x4 grid with central empty square
    # Layout (Aries is always at top-middle position):
    # [Pisces/12] [Aries/1] [Taurus/2] [Gemini/3]
    # [Aquarius/11] [EMPTY] [Cancer/4]
    # [Capricorn/10] [EMPTY] [Leo/5]
    # [Sagittarius/9] [Scorpio/8] [Libra/7] [Virgo/6]
    # Aries is always house 1 in the chart layout
    house_layout = [
        [12, 1, 2, 3],      # Top row (Pisces, Aries, Taurus, Gemini)
        [11, None, None, 4], # Second row (Aquarius, EMPTY, Cancer)
        [10, None, None, 5], # Third row (Capricorn, EMPTY, Leo)
        [9, 8, 7, 6]        # Bottom row (Sagittarius, Scorpio, Libra, Virgo)
    ]
    
    # Get rasi for each house in the chart
    # Aries is always house 1 in the chart layout
    rasi_list = list(RASI_NAMES.keys())
    aries_index = rasi_list.index('mesha') if 'mesha' in rasi_list else 0
    house_rasi = {}
    # Calculate rasi for each house position (Aries = house 1)
    for i in range(1, 13):
        rasi_index = (aries_index + i - 1) % 12
        house_rasi[i] = rasi_list[rasi_index]
    
    # Now map user's planets to chart houses
    # We need to convert from user's house system to chart house system
    user_house_to_chart_house = {}
    user_ascendant_house_in_chart = None
    if ascendant_rasi and ascendant_rasi in rasi_list:
        user_asc_index = rasi_list.index(ascendant_rasi)
        # Calculate offset from Aries
        if user_asc_index >= aries_index:
            offset = user_asc_index - aries_index
        else:
            offset = 12 - aries_index + user_asc_index
        
        # Map user's house numbers to chart house numbers
        for user_house in range(1, 13):
            chart_house = ((user_house - 1 + offset) % 12) + 1
            user_house_to_chart_house[user_house] = chart_house
        
        # User's ascendant (house 1) maps to this chart house
        user_ascendant_house_in_chart = user_house_to_chart_house.get(1, 1)
    
    # Group planets by chart house (not user's house)
    # Convert user's house numbers to chart house numbers
    house_planets = {}
    for planet, pos in positions.items():
        user_house = pos['house']
        # Convert to chart house number
        chart_house = user_house_to_chart_house.get(user_house, user_house)
        if chart_house not in house_planets:
            house_planets[chart_house] = []
        house_planets[chart_house].append({
            'name': planet,
            'degree': pos['degree'],
            'rasi': pos['rasi']
        })
    
    # Generate HTML
    html = """
    <div class="rasi-chart-container">
        <style>
            .rasi-chart {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                grid-template-rows: repeat(4, 1fr);
                gap: 2px;
                max-width: 600px;
                margin: 20px auto;
                border: 3px solid #000;
                background: #000;
            }
            .chart-cell {
                background: white;
                border: 2px solid #000;
                padding: 12px;
                min-height: 120px;
                position: relative;
                display: flex;
                flex-direction: column;
            }
            .chart-cell.empty {
                background: white;
                grid-column: span 1;
                grid-row: span 1;
            }
            .chart-cell.central-empty {
                grid-column: 2 / 4;
                grid-row: 2 / 4;
                background: white;
                border: 2px solid #000;
            }
            .chart-cell.user-ascendant {
                background: #fff9e6;
                border: 3px solid #ff6b6b;
                font-weight: bold;
            }
            # .chart-cell.user-ascendant .house-number::after {
            #     content: " (Your Ascendant)";
            #     color: #ff6b6b;
            #     font-size: 10px;
            # }
            .house-number {
                font-weight: bold;
                font-size: 12px;
                color: #666;
                margin-bottom: 4px;
            }
            .rasi-name {
                font-weight: bold;
                font-size: 14px;
                color: #333;
                margin-bottom: 6px;
                text-align: center;
            }
            .planet-list {
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            .planet-item {
                font-size: 13px;
                display: flex;
                align-items: center;
                gap: 5px;
            }
            .planet-symbol {
                font-size: 18px;
            }
            .planet-degree {
                color: #666;
                font-size: 11px;
            }
            .chart-title {
                text-align: center;
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 10px;
                color: #333;
            }
        </style>
        <div class="chart-title">South Indian Rasi Chart</div>
        <div class="rasi-chart">
    """
    
    # Calculate house numbers relative to user's ascendant
    # Map chart house number to user's house number
    chart_house_to_user_house = {}
    if user_house_to_chart_house:
        # Reverse the mapping
        for user_house, chart_house in user_house_to_chart_house.items():
            chart_house_to_user_house[chart_house] = user_house
    
    # Generate cells for the 4x4 grid
    central_empty_added = False
    for row_idx, row in enumerate(house_layout):
        for col_idx, house_num in enumerate(row):
            if house_num is None:
                # This is part of the central empty area
                # Only create one cell that spans 2x2 at position (1,1)
                if not central_empty_added and row_idx == 1 and col_idx == 1:
                    html += '<div class="chart-cell central-empty"></div>'
                    central_empty_added = True
                # Skip other None cells as they're covered by the central-empty
                continue
            
            rasi_name = RASI_NAMES.get(house_rasi.get(house_num, ''), '')
            planets_in_house = house_planets.get(house_num, [])
            
            # Get user's house number (starting from ascendant = 1)
            user_house_num = chart_house_to_user_house.get(house_num, house_num)
            
            cell_class = 'chart-cell'
            # Highlight user's ascendant house in the chart
            if house_num == user_ascendant_house_in_chart:
                cell_class += ' house-1 user-ascendant'
            
            html += f'<div class="{cell_class}">'
            html += f'<div class="house-number">House {user_house_num}</div>'
            html += f'<div class="rasi-name">{rasi_name}</div>'
            html += '<div class="planet-list">'
            
            if not planets_in_house:
                html += '<div class="planet-item" style="color: #999; font-style: italic;">Empty</div>'
            
            for planet_info in planets_in_house:
                planet_name = planet_info['name']
                degree = planet_info['degree']
                symbol = PLANET_SYMBOLS.get(planet_name, '')
                name = PLANET_NAMES.get(planet_name, planet_name.upper())
                
                # Format degree (degree is already within the sign, 0-30)
                deg_int = int(degree)
                deg_min = int((degree - deg_int) * 60)
                degree_str = f"{deg_int}° {deg_min:02d}'"
                
                html += f'''
                <div class="planet-item">
                    <!-- <span class="planet-symbol">{symbol}</span> -->
                    <span>{name}</span>
                    <span class="planet-degree">{degree_str}</span>
                </div>
                '''
            
            html += '</div></div>'
    
    html += """
        </div>
    </div>
    """
    
    return html

