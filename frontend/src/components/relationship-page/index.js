import React, { useState } from "react";
import { getScoreColor, capitalizeFirstLetter, getValue } from "../../utils/basic-logic";
import CardDetailRow from "../card-content/card";
import "../card-content/style.css";
import "./style.css";

const ScoreItem = ({ label, data, isHouse }) => {
  const [expanded, setExpanded] = useState(false);

  if (!data) {
    return (
      <div className="relationship-score-item">
        <span className="relationship-score-label">{label}</span>
        <span className="relationship-score-na">N/A</span>
      </div>
    );
  }

  const score = data.final_score;
  const name = isHouse
    ? `House ${data.house} (${capitalizeFirstLetter(data.rasi)})`
    : `${capitalizeFirstLetter(data.planet?.toLowerCase())} — ${capitalizeFirstLetter(data.rasi)} (House ${data.house})`;

  const isPlanet = !isHouse;
  const subathuvaValue = getValue(data.subathuva);
  const pabathuvamValue = getValue(data.pabathuvam);
  const hasBothEffects = subathuvaValue !== 0 && pabathuvamValue !== 0;
  const hasOnlySubathuva = subathuvaValue !== 0 && pabathuvamValue === 0;
  const hasOnlyPabathuvam = subathuvaValue === 0 && pabathuvamValue !== 0;

  const emoji = hasBothEffects ? "❤️" : hasOnlySubathuva ? "💚" : hasOnlyPabathuvam ? "🖤" : "💛";
  const emojiTitle = hasBothEffects ? "Has both Subathuva and Pabathuvam effects"
    : hasOnlySubathuva ? "Has only Subathuva effects"
    : hasOnlyPabathuvam ? "Has only Pabathuvam effects"
    : "Has no Subathuva or Pabathuvam effects";

  return (
    <div className="relationship-score-item-wrapper">
      <div
        className="relationship-score-item clickable"
        onClick={() => setExpanded((v) => !v)}
      >
        <span className="relationship-score-label">{label}</span>
        <span className="relationship-score-name">{name}</span>
        <span className="relationship-emoji-slot" title={emojiTitle}>
          {emoji}
        </span>
        <span
          className="relationship-score-badge"
          style={{ background: getScoreColor(score) }}
        >
          {score}
        </span>
        <span className="relationship-expand-icon">{expanded ? "▼" : "▶"}</span>
      </div>

      {expanded && (
        <div className="relationship-breakdown">
          <h4 className="breakdown-title">Score Breakdown</h4>
          <CardDetailRow label="Base Score" item={data.base} colorClass="positive" />
          <CardDetailRow label="Subathuva" item={data.subathuva} colorClass="positive" />
          <CardDetailRow label="Pabathuvam" item={data.pabathuvam} colorClass="negative" />
          {isHouse && (
            <>
              <CardDetailRow label="Planets in House" item={data.planets_in_house} colorClass="positive" />
              <CardDetailRow label="Benefic Aspects" item={data.benefic_aspects} colorClass="positive" />
              <CardDetailRow label="Malefic Aspects" item={data.malefic_aspects} colorClass="negative" />
              {data.planets_list && data.planets_list.length > 0 && (
                <div className="breakdown-planets">
                  <span className="breakdown-planets-label">Planets:</span>
                  {data.planets_list.map((p, i) => (
                    <span key={i} className="planet-tag">
                      {typeof p === "object" ? p.name : p}
                    </span>
                  ))}
                </div>
              )}
            </>
          )}
          {isPlanet && (
            <>
              <CardDetailRow label="Exaltation/Debilitation" item={data.exaltation_debilitation} colorClass={getValue(data.exaltation_debilitation) >= 0 ? "positive" : "negative"} />
              <CardDetailRow label="Friendship" item={data.friendship} colorClass="positive" />
              <CardDetailRow label="Special Houses" item={data.special_houses} colorClass="positive" />
              <CardDetailRow label="Position Bonus" item={data.position_bonus} colorClass="positive" />
              <CardDetailRow label="Drik Balam" item={data.drik_balam} colorClass={getValue(data.drik_balam) >= 0 ? "positive" : "negative"} />
              <CardDetailRow label="Planetary Exchange" item={data.planetery_exchange} colorClass="positive" />
              <CardDetailRow label="Exalt/Debil Conjunction" item={data.exalt_debil_conjunction} colorClass="positive" />
              <CardDetailRow label="Combust" item={data.combust} colorClass="negative" />
            </>
          )}
        </div>
      )}
    </div>
  );
};

const RelationshipPage = ({ relationship, onBack }) => {
  if (!relationship) {
    return (
      <div className="relationship-page">
        <div className="error-container">
          <p className="error-message">No relationship data available</p>
          <button className="back-button" onClick={onBack}>
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const { father, mother, younger_brother, younger_sister, spouse, children, elder_brother, elder_sister } = relationship;

  const members = [
    // Row 1: Father — Mother
    {
      title: "Father",
      items: [
        { label: "9th House", data: father?.ninth_house, isHouse: true },
        { label: "9th House Lord", data: father?.ninth_house_lord?.score, isHouse: false },
        { label: "Sun", data: father?.sun, isHouse: false },
        { label: "Simha House", data: father?.simha_house, isHouse: true },
      ],
    },
    {
      title: "Mother",
      items: [
        { label: "4th House", data: mother?.fourth_house, isHouse: true },
        { label: "4th House Lord", data: mother?.fourth_house_lord?.score, isHouse: false },
        { label: "Moon", data: mother?.moon, isHouse: false },
        { label: "Kadagam House", data: mother?.kadagam_house, isHouse: true },
      ],
    },
    // Row 2: Spouse — Children
    {
      title: "Spouse",
      items: [
        { label: "7th House", data: spouse?.seventh_house, isHouse: true },
        { label: "7th House Lord", data: spouse?.seventh_house_lord?.score, isHouse: false },
        { label: "Venus", data: spouse?.venus, isHouse: false },
        { label: "Vrishabha House", data: spouse?.vrishabha_house, isHouse: true },
        { label: "Thulam House", data: spouse?.thulam_house, isHouse: true },
      ],
    },
    {
      title: "Children",
      items: [
        { label: "5th House", data: children?.fifth_house, isHouse: true },
        { label: "5th House Lord", data: children?.fifth_house_lord?.score, isHouse: false },
        { label: "Jupiter", data: children?.jupiter, isHouse: false },
        { label: "Meena House", data: children?.meena_house, isHouse: true },
        { label: "Dhanu House", data: children?.dhanu_house, isHouse: true },
      ],
    },
    // Row 3: Younger Brother — Elder Brother
    {
      title: "Younger Brother",
      items: [
        { label: "3rd House", data: younger_brother?.third_house, isHouse: true },
        { label: "3rd House Lord", data: younger_brother?.third_house_lord?.score, isHouse: false },
        { label: "Mars", data: younger_brother?.mars, isHouse: false },
        { label: "Mesha House", data: younger_brother?.mesha_house, isHouse: true },
        { label: "Vrishchika House", data: younger_brother?.vrishchika_house, isHouse: true },
      ],
    },
    {
      title: "Elder Brother",
      items: [
        { label: "11th House", data: elder_brother?.eleventh_house, isHouse: true },
        { label: "11th House Lord", data: elder_brother?.eleventh_house_lord?.score, isHouse: false },
        { label: "Mars", data: elder_brother?.mars, isHouse: false },
        { label: "Mesha House", data: elder_brother?.mesha_house, isHouse: true },
        { label: "Vrishchika House", data: elder_brother?.vrishchika_house, isHouse: true },
      ],
    },
    // Row 4: Younger Sister — Elder Sister
    {
      title: "Younger Sister",
      items: [
        { label: "3rd House", data: younger_sister?.third_house, isHouse: true },
        { label: "3rd House Lord", data: younger_sister?.third_house_lord?.score, isHouse: false },
        { label: "Venus", data: younger_sister?.venus, isHouse: false },
        { label: "Vrishabha House", data: younger_sister?.vrishabha_house, isHouse: true },
        { label: "Thulam House", data: younger_sister?.thulam_house, isHouse: true },
      ],
    },
    {
      title: "Elder Sister",
      items: [
        { label: "11th House", data: elder_sister?.eleventh_house, isHouse: true },
        { label: "11th House Lord", data: elder_sister?.eleventh_house_lord?.score, isHouse: false },
        { label: "Venus", data: elder_sister?.venus, isHouse: false },
        { label: "Vrishabha House", data: elder_sister?.vrishabha_house, isHouse: true },
        { label: "Thulam House", data: elder_sister?.thulam_house, isHouse: true },
      ],
    },
  ];

  return (
    <div className="relationship-page">
      <div className="relationship-header">
        <button className="back-button" onClick={onBack}>
          ← Back to Home
        </button>
        <h1 className="page-title">Relationship Analysis</h1>
      </div>

      <div className="relationship-cards-container">
        {members.map((member) => (
          <div key={member.title} className="relationship-card">
            <div className="relationship-card-title">{member.title}</div>
            <div className="relationship-card-body">
              {member.items.map((item) => (
                <ScoreItem
                  key={item.label}
                  label={item.label}
                  data={item.data}
                  isHouse={item.isHouse}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RelationshipPage;
