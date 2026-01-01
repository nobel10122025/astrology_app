import React from "react";

import CardDetailRow from "./card";

import { getValue, getScoreColor } from '../../utils/basic-logic';
import { PLANET_SYMBOLS } from '../../utils/constants';

import "./style.css";

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
        const hasNoEffects = subathuvaValue === 0 && pabathuvamValue === 0;

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
                {hasBothEffects && (
                  <span
                    className="dual-effect-icon"
                    title="Has both Subathuva and Pabathuvam effects"
                  >
                    ❤️
                  </span>
                )}
                {hasNoEffects && (
                  <span
                    className="dual-effect-icon"
                    title="Has no Subathuva or Pabathuvam effects"
                  >
                    💚
                  </span>
                )}
              </div>
              <div
                className="score-badge"
                style={{ backgroundColor: scoreColor }}
              >
                {score.toFixed(2)}
              </div>
            </div>

            <div className="progress-container">
              <div
                className="progress-bar"
                style={{
                  width: `${normalizedScore}%`,
                  backgroundColor: scoreColor,
                }}
              />
            </div>
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
