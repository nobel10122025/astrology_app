import React from "react";

import CardDetailRow from "./card";

import { getValue, getScoreColor } from '../../utils/basic-logic';
import { PLANET_SYMBOLS } from '../../utils/constants';

import "./style.css";

// The three display tracks the backend now returns per planet (a regrouping of
// the score breakdown). Shown on planet cards instead of the single final_score.
const TRACK_ORDER = [
  { key: "subathuvam_papathuvam", label: "Subathuvam / Papathuvam" },
  { key: "dig_sthana", label: "Dig / Sthana" },
  { key: "kendra_kona", label: "Kendra / Kona" },
];
// Half-scale for the diverging track bars; a track rarely exceeds ±6.
const TRACK_MAX = 6;

const TrackMeter = ({ label, value }) => {
  const v = Math.max(-TRACK_MAX, Math.min(TRACK_MAX, value || 0));
  const half = (Math.abs(v) / TRACK_MAX) * 50;
  const left = v >= 0 ? 50 : 50 - half;
  const cls = value > 0 ? "pos" : value < 0 ? "neg" : "zero";
  return (
    <div className="ptrack-row">
      <span className="ptrack-label">{label}</span>
      <div className="ptrack-bar">
        <span className="ptrack-center" />
        <span
          className={`ptrack-fill ${cls}`}
          style={{ left: `${left}%`, width: `${half}%` }}
        />
      </div>
      <span className={`ptrack-val ${cls}`}>
        {value > 0 ? `+${value}` : value}
      </span>
    </div>
  );
};

const CardContent = ({ results, expandItem, toggle, is_planet_card }) => {
  return (
    <div className="planet-cards-grid">
      {results.map((item, index) => {
        const isExpanded = expandItem.has(
          is_planet_card ? item.planet : item.house
        );
        const score = getValue(item.final_score);
        const normalizedScore = ((score + 5) / 20) * 100;
        const scoreColor = getScoreColor(score);

        // Check if both subathuva and pabathuvam are not 0
        const subathuvaValue = getValue(item.subathuva);
        const pabathuvamValue = getValue(item.pabathuvam);
        const hasBothEffects = subathuvaValue !== 0 && pabathuvamValue !== 0;
        const hasOnlySubathuva = subathuvaValue !== 0 && pabathuvamValue === 0;
        const hasOnlyPabathuvam = subathuvaValue === 0 && pabathuvamValue !== 0;
        const emoji = hasBothEffects ? "❤️" : hasOnlySubathuva ? "💚" : hasOnlyPabathuvam ? "🖤" : "💛";
        const emojiTitle = hasBothEffects ? "Has both Subathuva and Pabathuvam effects"
          : hasOnlySubathuva ? "Has only Subathuva effects"
          : hasOnlyPabathuvam ? "Has only Pabathuvam effects"
          : "Has no Subathuva or Pabathuvam effects";

        return (
          <div
            key={index}
            className={`planet-card ${isExpanded ? "expanded" : ""}`}
            onClick={() => {
              toggle(is_planet_card ? item.planet : item.house);
            }}
          >
            <div className="card-header">
              <div className="planet-info">
                <span className="planet-symbol">🏠</span>
                <span className="planet-name">
                  {" "}
                  {is_planet_card ? "Planet" : "House"}{" "}
                  {is_planet_card ? item.planet : item.house}
                </span>
                <span className="dual-effect-icon" title={emojiTitle}>
                  {emoji}
                </span>
              </div>
              {/* final_score is kept internally but shown only for houses;
                  planet cards display the 3 tracks below instead. */}
              {!is_planet_card && (
                <div
                  className="score-badge"
                  style={{ backgroundColor: scoreColor }}
                >
                  {score.toFixed(2)}
                </div>
              )}
            </div>

            {!is_planet_card && (
              <div className="progress-container">
                <div
                  className="progress-bar"
                  style={{
                    width: `${normalizedScore}%`,
                    backgroundColor: scoreColor,
                  }}
                />
              </div>
            )}
            {!is_planet_card && (
              <div className="planet-quick-info">
                <div className="info-item">
                  <span className="info-label">Rasi:</span>
                  <span className="info-value">{item.rasi}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Planets:</span>
                  <span className="info-value">
                    {getValue(item.planets_in_house)}
                  </span>
                </div>
              </div>
            )}
            {is_planet_card && (
              <div className="planet-quick-info">
                <div className="info-item">
                  <span className="info-label">Rasi:</span>
                  <span className="info-value">{item.rasi}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">House:</span>
                  <span className="info-value">{item.house}</span>
                </div>
              </div>
            )}

            {is_planet_card && item.tracks && (
              <div className="planet-tracks">
                {TRACK_ORDER.map((t) => (
                  <TrackMeter
                    key={t.key}
                    label={t.label}
                    value={getValue(item.tracks[t.key])}
                  />
                ))}
                {item.mutual_exchange?.active && (
                  <div
                    className="mutual-exchange-badge"
                    title={item.mutual_exchange.reason}
                  >
                    🔄 {item.mutual_exchange.reason || "Mutual exchange"}
                  </div>
                )}
              </div>
            )}

            {isExpanded && (
              <div className="card-details">
                <div className="detail-section">
                  <h4>Score Breakdown</h4>
                  <CardDetailRow
                    label="Base Score"
                    item={item.base}
                    colorClass="positive"
                  />
                  <CardDetailRow
                    label="Subathuva"
                    item={item.subathuva}
                    colorClass="positive"
                  />
                  <CardDetailRow
                    label="Pabathuvam"
                    item={item.pabathuvam}
                    colorClass="negative"
                  />
                  <CardDetailRow
                    label="Benefic Aspects"
                    item={item.benefic_aspects}
                    colorClass="positive"
                  />
                  <CardDetailRow
                    label="Malefic Aspects"
                    item={item.malefic_aspects}
                    colorClass="negative"
                  />
                  {is_planet_card && (
                    <>
                      <CardDetailRow
                        label="Exaltation/Debilitation"
                        item={item.exaltation_debilitation}
                        colorClass={
                          getValue(item.exaltation_debilitation) > 0
                            ? "positive"
                            : "negative"
                        }
                      />
                      <CardDetailRow
                        label="Friendship"
                        item={item.friendship}
                        colorClass="positive"
                      />
                      <CardDetailRow
                        label="Planetery Exchange"
                        item={item.planetery_exchange}
                        colorClass="positive"
                      />
                      <CardDetailRow
                        label="Position Bonus"
                        item={item.position_bonus}
                        colorClass={"positive"}
                      />
                      <CardDetailRow
                        label="Special Houses"
                        item={item.special_houses}
                        colorClass="positive"
                      />
                      <CardDetailRow
                        label="Drik Balam"
                        item={item.drik_balam}
                        colorClass={
                          getValue(item.drik_balam) > 0 ? "positive" : "negative"
                        }
                      />
                      <CardDetailRow
                        label="Exaltation/Debilitation Conjunction"
                        item={item.exalt_debil_conjunction}
                        colorClass="positive"
                      />
                      <CardDetailRow
                        label="Combust"
                        item={item.combust}
                        colorClass="negative"
                      />
                    </>
                  )}
                </div>
                {!is_planet_card &&
                  item.planets_list &&
                  item.planets_list.length > 0 && (
                    <div className="detail-section">
                      <h4>Planets in House</h4>
                      <div className="planets-list">
                        {item.planets_list.map((planet, idx) => {
                          // Handle both old format (string) and new format (object)
                          const planetName =
                            typeof planet === "object" &&
                            planet !== null &&
                            planet.name
                              ? planet.name
                              : typeof planet === "string"
                              ? planet
                              : "";
                          const ownedHouses =
                            typeof planet === "object" &&
                            planet !== null &&
                            planet.owned_houses
                              ? planet.owned_houses
                              : [];
                          const displayName = planetName.toUpperCase();
                          return (
                            <span key={idx} className="planet-tag">
                              {PLANET_SYMBOLS[displayName] || "●"} {displayName}
                              {ownedHouses && ownedHouses.length > 0 && (
                                <span className="owned-houses">
                                  {" "}
                                  (Owns: {ownedHouses.join(", ")})
                                </span>
                              )}
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  )}
              </div>
            )}

            <div className="expand-indicator">
              {expandItem.has(item.house) ? "▼ Less" : "▶ More"}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default CardContent;
