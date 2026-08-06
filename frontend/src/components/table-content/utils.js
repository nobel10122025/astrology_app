// Planet table now reflects the point-scale model: Subathuvam (benefic sum),
// Papathuvam (malefic sum) and Sthana/Dig (placement) shown separately, plus
// the collapsed Strength on the -5..15 scale used everywhere else.
const planetTableHeaders = [
    { label: "Planet", key: "planet", positive: false, negative: false },
    { label: "Absolute Degree", key: "absolute_degree", positive: false, negative: false },
    { label: "Rasi", key: "rasi", positive: false, negative: false },
    { label: "House", key: "house", positive: false, negative: false },
    { label: "Subathuvam", key: "subathuvam", positive: true, negative: false },
    { label: "Papathuvam", key: "papathuvam", positive: false, negative: true },
    { label: "Sthana / Dig", key: "sthana", positive: true, negative: false },
    { label: "Net Contact", key: "net_contact", positive: true, negative: true, threshold: 0 },
    { label: "Strength", key: "strength_score", positive: true, negative: true, threshold: 5 }
];

// House table on the point-scale: houses are scored purely by the planets that
// occupy / aspect them (Subathuvam vs Papathuvam) - no Sthana / lord dignity.
const houseTableHeaders = [
    { label: "House", key: "house", positive: false, negative: false },
    { label: "Rasi", key: "rasi", positive: false, negative: false },
    { label: "Subathuvam", key: "subathuvam", positive: true, negative: false },
    { label: "Papathuvam", key: "papathuvam", positive: false, negative: true },
    { label: "Net Contact", key: "net_contact", positive: true, negative: true, threshold: 0 },
    { label: "Strength", key: "strength_score", positive: true, negative: true, threshold: 5 }
];

export { planetTableHeaders, houseTableHeaders };