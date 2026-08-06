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


def generate_south_indian_chart(data, results, house_strengths=None):
    """
    Generate South Indian style Rasi chart HTML
    Layout: South Indian style with house 1 at bottom-left

    house_strengths: optional {user_house_num: {'net','strength','subathuvam',
    'papathuvam'}} from the point-scale house model. When given, each house cell
    is tinted benefic/malefic by its net contact and shows a small net badge.
    """
    house_strengths = house_strengths or {}
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
    
    # Generate HTML. Colours pull from the app's theme CSS variables (which
    # cascade into this injected markup) with sensible fallbacks.
    html = """
    <div class="rasi-chart-container">
        <style>
            .rasi-chart-container {
                --chart-pos: var(--benefic, #2e7d51);
                --chart-neg: var(--malefic, #c0492f);
                --chart-surface: var(--surface, #ffffff);
                --chart-ink: var(--ink, #23201c);
                --chart-faint: var(--ink-faint, #8a8178);
                --chart-line: var(--line, #e4dccb);
                --chart-accent: var(--theme-primary, #b08637);
            }
            .rasi-chart {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                grid-template-rows: repeat(4, 1fr);
                gap: 6px;
                max-width: 620px;
                margin: 20px auto;
                padding: 6px;
                border-radius: 16px;
                background: var(--chart-line);
                box-shadow: 0 8px 22px rgba(0, 0, 0, 0.08);
            }
            .chart-cell {
                background: var(--chart-surface);
                color: var(--chart-ink);
                border: 1px solid var(--chart-line);
                border-radius: 10px;
                padding: 10px;
                min-height: 118px;
                position: relative;
                display: flex;
                flex-direction: column;
                transition: transform 0.15s ease, box-shadow 0.15s ease;
            }
            .chart-cell:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 18px rgba(0, 0, 0, 0.12);
                z-index: 2;
            }
            .chart-cell.central-empty {
                grid-column: 2 / 4;
                grid-row: 2 / 4;
                background: transparent;
                border: none;
                box-shadow: none;
                align-items: center;
                justify-content: center;
            }
            .chart-cell.central-empty:hover { transform: none; box-shadow: none; }
            .chart-cell.user-ascendant {
                outline: 2px solid var(--chart-accent);
                outline-offset: -2px;
            }
            .cell-head {
                display: flex;
                align-items: baseline;
                justify-content: space-between;
                gap: 6px;
                margin-bottom: 2px;
            }
            .house-number {
                font-weight: 700;
                font-size: 11px;
                letter-spacing: 0.03em;
                color: var(--chart-faint);
            }
            .house-net {
                font-size: 11px;
                font-weight: 800;
                font-variant-numeric: tabular-nums;
            }
            .house-net.pos { color: var(--chart-pos); }
            .house-net.neg { color: var(--chart-neg); }
            .house-net.zero { color: var(--chart-faint); }
            .rasi-name {
                font-weight: 700;
                font-size: 13px;
                color: var(--chart-ink);
                margin-bottom: 6px;
            }
            .planet-list {
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 3px;
            }
            .planet-item {
                font-size: 12.5px;
                display: flex;
                align-items: center;
                gap: 5px;
            }
            .planet-degree {
                color: var(--chart-faint);
                font-size: 10.5px;
            }
            .chart-asc-planet { color: var(--chart-accent); font-weight: 700; }
            .chart-title {
                text-align: center;
                font-family: var(--font-display, inherit);
                font-size: 20px;
                font-weight: 700;
                margin-bottom: 6px;
                color: var(--chart-ink);
            }
            .chart-legend {
                text-align: center;
                font-size: 11px;
                color: var(--chart-faint);
                margin-bottom: 8px;
            }
            .chart-legend .pos { color: var(--chart-pos); font-weight: 700; }
            .chart-legend .neg { color: var(--chart-neg); font-weight: 700; }
        </style>
        <div class="chart-title">South Indian Rasi Chart</div>
        <div class="chart-legend">House tint &amp; net = Subathuvam <span class="pos">(+)</span> vs Papathuvam <span class="neg">(&minus;)</span></div>
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

            # Point-scale tint + net badge for this house (if strengths provided)
            strength = house_strengths.get(user_house_num)
            cell_style = ''
            net_badge = ''
            if strength is not None:
                net = strength.get('net', 0) or 0
                # intensity 0..1 of |net|, capped so text stays readable
                pct = min(abs(net), 200) / 200 * 55
                if net > 0:
                    cell_style = (f' style="background: color-mix(in srgb, '
                                  f'var(--chart-pos) {pct:.0f}%, var(--chart-surface));"')
                    net_badge = f'<span class="house-net pos">+{net:g}</span>'
                elif net < 0:
                    cell_style = (f' style="background: color-mix(in srgb, '
                                  f'var(--chart-neg) {pct:.0f}%, var(--chart-surface));"')
                    net_badge = f'<span class="house-net neg">{net:g}</span>'
                else:
                    net_badge = '<span class="house-net zero">0</span>'

            html += f'<div class="{cell_class}"{cell_style}>'
            html += ('<div class="cell-head">'
                     f'<span class="house-number">House {user_house_num}</span>'
                     f'{net_badge}</div>')
            html += f'<div class="rasi-name">{rasi_name}</div>'
            html += '<div class="planet-list">'

            if not planets_in_house:
                html += '<div class="planet-item" style="color: var(--chart-faint); font-style: italic;">Empty</div>'

            for planet_info in planets_in_house:
                planet_name = planet_info['name']
                degree = planet_info['degree']
                name = PLANET_NAMES.get(planet_name, planet_name.upper())
                name_class = 'chart-asc-planet' if planet_name == 'ascendant' else ''

                # Format degree (degree is already within the sign, 0-30)
                deg_int = int(degree)
                deg_min = int((degree - deg_int) * 60)
                degree_str = f"{deg_int}° {deg_min:02d}'"

                html += f'''
                <div class="planet-item">
                    <span class="{name_class}">{name}</span>
                    <span class="planet-degree">{degree_str}</span>
                </div>
                '''

            html += '</div></div>'
    
    html += """
        </div>
    </div>
    """
    
    return html

