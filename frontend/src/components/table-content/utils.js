const planetTableHeaders = [
    { label: "Planet", key: "planet", positive: false, negative: false },
    { label: "Absolute Degree", key: "absolute_degree", positive: false, negative: false },
    { label: "Rasi", key: "rasi", positive: false, negative: false },
    { label: "House", key: "house", positive: false, negative: false },
    { label: "Base", key: "base", positive: false, negative: false },
    { label: "Subathuva", key: "subathuva", positive: true, negative: false },
    { label: "Pabathuvam", key: "pabathuvam", positive: false, negative: true },
    { label: "Position", key: "position", positive: false, negative: false },
    { label: "Planetery Exchange", key: "planetery_exchange", positive: true, negative: false },
    { label: "Exalt/Debil", key: "exaltation_debilitation", positive: true, negative: false },
    { label: "Friendship", key: "friendship", positive: false, negative: false },
    { label: "Special Houses", key: "special_houses", positive: false, negative: false },
    { label: "Drik Balam", key: "drik_balam", positive: true, negative: true },
    { label: "Mutual Aspect", key: "mutual_aspect", positive: false, negative: false },
    { label: "Exalt/Debil Conj", key: "exalt_debil_conjunction", positive: true, negative: false },
    { label: "Combust", key: "combust", positive: false, negative: false },
    { label: "Final Score", key: "final_score", positive: true, negative: true }
];

const houseTableHeaders = [
    { label: "House", key: "house", positive: false, negative: false },
    { label: "Rasi", key: "rasi", positive: false, negative: false },
    { label: "Base", key: "base", positive: false, negative: false },
    { label: "Subathuva", key: "subathuva", positive: true, negative: false },
    { label: "Pabathuvam", key: "pabathuvam", positive: false, negative: true },
    { label: "Planets in House", key: "planets_in_house", positive: false, negative: false },
    { label: "Benefic Aspects", key: "benefic_aspects", positive: true, negative: false },    
    { label: "Malefic Aspects", key: "malefic_aspects", positive: false, negative: true },
    { label: "Final Score", key: "final_score", positive: true, negative: true }
];

export { planetTableHeaders, houseTableHeaders };