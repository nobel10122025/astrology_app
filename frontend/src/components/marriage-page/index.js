import React, { useState } from "react";
import { getScoreColor, capitalizeFirstLetter, getValue } from "../../utils/basic-logic";
import CardDetailRow from "../card-content/card";
import "../card-content/style.css";
import "./style.css";

const ScoreRow = ({ label, data, isHouse }) => {
  const [expanded, setExpanded] = useState(false);

  if (!data) {
    return (
      <tr className="marriage-row">
        <td className="marriage-cell-label">{label}</td>
        <td className="marriage-cell-detail">—</td>
        <td className="marriage-cell-score">—</td>
      </tr>
    );
  }

  const score = data.final_score;
  const detail = isHouse
    ? `House ${data.house} (${capitalizeFirstLetter(data.rasi)})`
    : data.planet
    ? `${capitalizeFirstLetter(data.planet.toLowerCase())} — ${capitalizeFirstLetter(data.rasi)} (House ${data.house})`
    : `${capitalizeFirstLetter(data.rasi)} (House ${data.house})`;

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
    <>
      <tr
        className="marriage-row clickable"
        onClick={() => setExpanded((v) => !v)}
      >
        <td className="marriage-cell-label">{label}</td>
        <td className="marriage-cell-detail">{detail}</td>
        <td className="marriage-cell-score">
          <span className="marriage-emoji-slot" title={emojiTitle}>
            {emoji}
          </span>
          <span
            className="marriage-score-badge"
            style={{ background: getScoreColor(score) }}
          >
            {score}
          </span>
          <span className="marriage-expand-icon">{expanded ? "▼" : "▶"}</span>
        </td>
      </tr>
      {expanded && (
        <tr className="marriage-breakdown-row">
          <td colSpan={3}>
            <div className="marriage-breakdown">
              <div className="breakdown-title">Score Breakdown</div>
              <CardDetailRow label="Base Score" item={data.base} colorClass="positive" />
              <CardDetailRow label="Subathuva" item={data.subathuva} colorClass="positive" />
              <CardDetailRow label="Pabathuvam" item={data.pabathuvam} colorClass="negative" />
              {isHouse && (
                <>
                  <CardDetailRow label="Planets in House" item={data.planets_in_house} colorClass="positive" />
                  <CardDetailRow label="Benefic Aspects" item={data.benefic_aspects} colorClass="positive" />
                  <CardDetailRow label="Malefic Aspects" item={data.malefic_aspects} colorClass="negative" />
                  {data.planets_list?.length > 0 && (
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
          </td>
        </tr>
      )}
    </>
  );
};

const MarriageSection = ({ title, rows }) => (
  <div className="marriage-section">
    <div className="marriage-section-title">{title}</div>
    <table className="marriage-table">
      <thead>
        <tr>
          <th className="marriage-th">Indicator</th>
          <th className="marriage-th">Detail</th>
          <th className="marriage-th">Score</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <ScoreRow key={row.label} label={row.label} data={row.data} isHouse={row.isHouse} />
        ))}
      </tbody>
    </table>
  </div>
);

const MarriagePage = ({ marriage, onBack }) => {
  if (!marriage) {
    return (
      <div className="marriage-page">
        <div className="error-container">
          <p className="error-message">No marriage data available</p>
          <button className="back-button" onClick={onBack}>Go Back</button>
        </div>
      </div>
    );
  }

  const { from_lagna, from_moon, key_indicators } = marriage;

  const sections = [
    {
      title: "From Lagna",
      rows: [
        { label: "2nd House", data: from_lagna?.second_house, isHouse: true },
        { label: "7th House", data: from_lagna?.seventh_house, isHouse: true },
        { label: "8th House", data: from_lagna?.eighth_house, isHouse: true },
      ],
    },
    {
      title: "From Moon",
      rows: [
        { label: "2nd from Moon", data: from_moon?.second_house, isHouse: true },
        { label: "7th from Moon", data: from_moon?.seventh_house, isHouse: true },
        { label: "8th from Moon", data: from_moon?.eighth_house, isHouse: true },
      ],
    },
    {
      title: "Key Indicators",
      rows: [
        { label: "7th House", data: key_indicators?.seventh_house, isHouse: true },
        { label: "7th House Lord", data: key_indicators?.seventh_house_lord?.score, isHouse: false },
        { label: "Venus", data: key_indicators?.venus, isHouse: false },
      ],
    },
  ];

  return (
    <div className="marriage-page">
      <div className="marriage-header">
        <button className="back-button" onClick={onBack}>← Back to Home</button>
        <h1 className="page-title">Marriage Analysis</h1>
      </div>

      <div className="marriage-sections-container">
        {sections.map((section) => (
          <MarriageSection key={section.title} title={section.title} rows={section.rows} />
        ))}
      </div>
    </div>
  );
};

export default MarriagePage;
