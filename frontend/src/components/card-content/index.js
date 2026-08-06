import React from "react";

import CardDetailRow from "./card";

import { getValue, getScoreColor } from '../../utils/basic-logic';
import { PLANET_SYMBOLS } from '../../utils/constants';

import "./style.css";

// Full-width scale for the diverging Subathuvam/Papathuvam bar. Track 1 is a
// net signed contact balance; it rarely exceeds +/-200 on the new point scale.
const TRACK1_MAX = 200;

// Dignity tier -> chip colour class (see style.css).
const DIGNITY_CLASS = {
  neecha_bhanga: "dig-great",
  exalted: "dig-great",
  moolatrikona: "dig-good",
  own: "dig-good",
  friend: "dig-mid",
  neutral: "dig-mid",
  enemy: "dig-bad",
  debilitated: "dig-bad",
  none: "dig-none",
};

const prettyDignity = (d) =>
  (d || "none").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

// Track 2 (planets only): placement strength as a labelled chip (not a bar).
// Houses have no Sthana track, so this renders nothing for them.
const DignityChip = ({ track }) => {
  if (!track) return null;
  const cls = DIGNITY_CLASS[track.dignity] || "dig-none";
  return (
    <div className="track-line">
      <span className="track-name">Sthana / Dig</span>
      <span className={`dignity-chip ${cls}`}>
        <span className="dignity-tier">
          {prettyDignity(track.dignity)}
          {track.dig_bala ? " · +Dig" : ""}
        </span>
        <span className="dignity-val">{track.value}</span>
      </span>
    </div>
  );
};

// Track 1: benefic (Subathuvam) and malefic (Papathuvam) as TWO separate
// scores. The diverging bar fills green from centre by Subathuvam and red by
// Papathuvam at the same time, and both totals are shown as numbers.
const SubaPapaBar = ({ track }) => {
  const sub = track ? getValue(track.subathuvam) : 0;   // >= 0
  const pap = track ? getValue(track.papathuvam) : 0;   // <= 0
  const posHalf = (Math.min(Math.abs(sub), TRACK1_MAX) / TRACK1_MAX) * 50;
  const negHalf = (Math.min(Math.abs(pap), TRACK1_MAX) / TRACK1_MAX) * 50;
  return (
    <div className="track-block">
      <div className="suba-papa-head">
        <span className="track-name">Subathuvam / Papathuvam</span>
        <span className="suba-papa-vals">
          <span className="diverge-val pos">+{sub}</span>
          <span className="diverge-val neg">{pap}</span>
        </span>
      </div>
      <div className="diverge-bar">
        <span className="diverge-center" />
        <span className="diverge-fill pos" style={{ left: "50%", width: `${posHalf}%` }} />
        <span className="diverge-fill neg" style={{ right: "50%", width: `${negHalf}%` }} />
      </div>
    </div>
  );
};

// Expanded view: the point facts that produced a track's value.
const FactSection = ({ title, track }) => {
  if (!track) return null;
  const facts = track.facts || [];
  // Track 1 shows the two split totals; other tracks show their single value.
  const isSplit = track.subathuvam !== undefined || track.papathuvam !== undefined;
  return (
    <div className="detail-section">
      <h4>
        {title}
        <span className="section-total">
          {isSplit ? (
            <>
              <span className="pos">+{getValue(track.subathuvam)}</span>
              {" / "}
              <span className="neg">{getValue(track.papathuvam)}</span>
            </>
          ) : getValue(track.value) > 0 ? (
            `+${getValue(track.value)}`
          ) : (
            getValue(track.value)
          )}
        </span>
      </h4>
      {facts.length === 0 ? (
        <div className="detail-row"><span>No contributing factors</span></div>
      ) : (
        facts.map((f, i) => {
          const val = getValue(f.value);
          return (
            <div className="detail-row" key={i}>
              <span>{f.note}</span>
              <span className={`value ${val > 0 ? "positive" : val < 0 ? "negative" : ""}`}>
                {val > 0 ? `+${val}` : val}
              </span>
            </div>
          );
        })
      )}
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
        // Houses now carry the point-scale strength (mapped onto -5..15); fall
        // back to the legacy final_score if it is missing.
        const score = getValue(item.strength_score ?? item.final_score);
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
                {!is_planet_card && <span className="planet-symbol">🏠</span>}
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
                  planet cards display the two tracks below instead. */}
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

            {item.tracks && (
              <div className="planet-tracks">
                <DignityChip track={item.tracks.dig_sthana} />
                <SubaPapaBar track={item.tracks.subathuvam_papathuvam} />
              </div>
            )}

            {isExpanded && (
              <div className="card-details">
                {item.tracks ? (
                  <>
                    <FactSection
                      title="Subathuvam / Papathuvam"
                      track={item.tracks?.subathuvam_papathuvam}
                    />
                    <FactSection
                      title="Sthana / Dig Balam"
                      track={item.tracks?.dig_sthana}
                    />
                  </>
                ) : (
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
                  </div>
                )}

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
