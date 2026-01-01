# Rasi to degree mapping (0-360 degrees)
RASI_TO_DEGREE = {
    'mesha': (0, 30),      # Aries
    'vrishabha': (30, 60),  # Taurus
    'mithuna': (60, 90),    # Gemini
    'karka': (90, 120),     # Cancer
    'simha': (120, 150),    # Leo
    'kanya': (150, 180),    # Virgo
    'tula': (180, 210),     # Libra
    'vrishchika': (210, 240), # Scorpio
    'dhanu': (240, 270),    # Sagittarius
    'makara': (270, 300),   # Capricorn
    'kumbha': (300, 330),   # Aquarius
    'meena': (330, 360)     # Pisces
}

# Planet exaltation and debilitation signs
PLANET_EXALTATION = {
    'sun': 'mesha',      # Exalted in Aries
    'moon': 'vrishabha', # Exalted in Taurus
    'mars': 'makara',    # Exalted in Capricorn
    'mercury': 'kanya',  # Exalted in Virgo
    'jupiter': 'karka',  # Exalted in Cancer
    'venus': 'meena',    # Exalted in Pisces
    'saturn': 'tula'     # Exalted in Libra
}

PLANET_DEBILITATION = {
    'sun': 'tula',       # Debilitated in Libra
    'moon': 'vrishchika', # Debilitated in Scorpio
    'mars': 'karka',     # Debilitated in Cancer
    'mercury': 'meena',  # Debilitated in Pisces
    'jupiter': 'makara', # Debilitated in Capricorn
    'venus': 'kanya',    # Debilitated in Virgo
    'saturn': 'mesha'    # Debilitated in Aries
}

# Own houses (Moolatrikona)
PLANET_OWN_HOUSES = {
    'sun': ['simha'],
    'moon': ['karka'],
    'mars': ['mesha', 'vrishchika'],
    'mercury': ['mithuna', 'kanya'],
    'jupiter': ['dhanu', 'meena'],
    'venus': ['vrishabha', 'tula'],
    'saturn': ['makara', 'kumbha']
}

# Friendly, enemy, neutral relationships
PLANET_RELATIONSHIPS = {
    'sun': {'friend': ['moon', 'mars', 'jupiter'], 'enemy': ['venus', 'saturn'], 'neutral': ['mercury']},
    'moon': {'friend': ['sun', 'mercury'], 'enemy': [], 'neutral': ['mars', 'jupiter', 'venus', 'saturn']},
    'mars': {'friend': ['sun', 'moon', 'jupiter'], 'enemy': ['mercury'], 'neutral': ['venus', 'saturn']},
    'mercury': {'friend': ['sun', 'venus'], 'enemy': ['moon'], 'neutral': ['mars', 'jupiter', 'saturn']},
    'jupiter': {'friend': ['sun', 'moon', 'mars'], 'enemy': ['mercury', 'venus'], 'neutral': ['saturn']},
    'venus': {'friend': ['mercury', 'saturn'], 'enemy': ['sun', 'moon'], 'neutral': ['mars', 'jupiter']},
    'saturn': {'friend': ['mercury', 'venus'], 'enemy': ['sun', 'moon', 'mars'], 'neutral': ['jupiter']}
}

PLANETS = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
HOUSES = ['mesha', 'vrishabha', 'mithuna', 'karka', 'simha', 'kanya', 'tula', 'vrishchika', 'dhanu', 'makara', 'kumbha', 'meena']

DRIK_BALAM_LOGIC = {
    'sun': {
        "gain": 10,
        "loss": 4,
    },
    "moon": {
        "gain": 4,
        "loss": 10,
    },
    "mars": {
        "gain": 10,
        "loss": 4,
    },
    "mercury": {
        "gain": 1,
        "loss": 7,
    },
    "jupiter": {
        "gain": 1,
        "loss": 7,
    },
    "venus": {
        "gain": 4,
        "loss": 10,
    },
    "saturn": {
        "gain": 7,
        "loss": 1,
    },
}

# Detailed profession categories for planets based on Vedic astrology
PLANET_PROFESSIONS = {
    'mars': [
        'Uniformed services',
        'Medical fields',
        'Construction',
        'civil engineering',
        'Sports, fitness',
        'Firefighting',
        'meat and butchery',
        'bakeries and fast food',
    ],
    'sun': [
        'politics',
        'government job',
        'leadership related',
        'electricity related',
    ],
    'jupiter': [
        'Teaching',
        'Banking',
        'Gold trading',
        'Judiciary roles',
        'Religious activities'
    ],
    'mercury': [
        'IT (Information Technology)',
        'Mass media',
        'Education',
        'Astrology',
        'Writing',
        'Accountancy',
        'Communication-related jobs'
    ],
    'saturn': [
        'mechanical engineering',
        'philosophy',
        'crushing industries',
        'mining',
        'quarrying',
        'domestic cleaning',
        'sanitation',
    ],
    'venus': [
        'women related',
        'beauty related',
        'silver jewelry',
        'hospitality',
        'luxury (hotel, restaurant, etc)',
        'comfort (furniture, bedding, etc)',
        'arts and crafts (painting, sculpture, etc)',
    ],
    'moon': [
        'liquids (milk, juice, water, etc) businesses',
        'marine, water, river, sea, etc',
        'vegetables, rice, lentils, etc',
        'cooking',
        'psychiatry',
    ]
}

COMBUST_DEGREES = {
    'venus': 9,
    'jupiter': 11,
    'mercury': 13,
    'mars': 15,
    'saturn': 17,
}

# Nakshatra information: (start_degree, name, dasha_lord)
# Each nakshatra spans 13.333 degrees (13°20')
NAKSHATRAS = [
    (0, 'Ashwini', 'ketu'),
    (13.333, 'Bharani', 'venus'),
    (26.667, 'Krittika', 'sun'),
    (40, 'Rohini', 'moon'),
    (53.333, 'Mrigashira', 'mars'),
    (66.667, 'Ardra', 'rahu'),
    (80, 'Punarvasu', 'jupiter'),
    (93.333, 'Pushya', 'saturn'),
    (106.667, 'Ashlesha', 'mercury'),
    (120, 'Magha', 'ketu'),
    (133.333, 'Purva Phalguni', 'venus'),
    (146.667, 'Uttara Phalguni', 'sun'),
    (160, 'Hasta', 'moon'),
    (173.333, 'Chitra', 'mars'),
    (186.667, 'Swati', 'rahu'),
    (200, 'Vishakha', 'jupiter'),
    (213.333, 'Anuradha', 'saturn'),
    (226.667, 'Jyeshta', 'mercury'),
    (240, 'Mula', 'ketu'),
    (253.333, 'Purva Ashadha', 'venus'),
    (266.667, 'Uttara Ashadha', 'sun'),
    (280, 'Shravana', 'moon'),
    (293.333, 'Dhanishta', 'mars'),
    (306.667, 'Shatabhisha', 'rahu'),
    (320, 'Purva Bhadrapada', 'jupiter'),
    (333.333, 'Uttara Bhadrapada', 'saturn'),
    (346.667, 'Revati', 'mercury')
]

# Dasha periods in years
DASHA_PERIODS = {
    'ketu': 7,
    'venus': 20,
    'sun': 6,
    'moon': 10,
    'mars': 7,
    'rahu': 18,
    'jupiter': 16,
    'saturn': 19,
    'mercury': 17
}

# Dasha sequence (Vimshottari Dasha order)
DASHA_SEQUENCE = ['ketu', 'venus', 'sun', 'moon', 'mars', 'rahu', 'jupiter', 'saturn', 'mercury']

TAMIL_YEAR = 365.25