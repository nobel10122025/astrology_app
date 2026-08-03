import React from "react";
import "./style.css";

const titleize = (s) =>
  (s || "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

const scoreClass = (score) => {
  if (score == null) return "score-unknown";
  if (score >= 6.5) return "score-high";
  if (score >= 4.5) return "score-mid";
  return "score-low";
};

// Each applied-rule reason comes prefixed with its verdict: "[favourable] ...".
const VERDICT_RE = /^\[(favourable|unfavourable|neutral|info|n\/a)\]\s*/;
const splitReason = (r) => {
  const m = (r || "").match(VERDICT_RE);
  return {
    verdict: m ? m[1] : "neutral",
    text: (r || "").replace(VERDICT_RE, ""),
  };
};

// The DasaFavourability sub-agent verdict for the CURRENT maha+bhukti period.
const DashaCard = ({ dasha, narrative, currentAge, activeDasha }) => {
  if (!dasha || !dasha.available) return null;

  const maha = dasha.maha || {};
  const bhukti = dasha.bhukti || null;
  const score = dasha.combined_score;
  const pct = score != null ? Math.round((score / 10) * 100) : 0;
  const reasons = (maha.reasons || []).map(splitReason);
  const nar = narrative?.domains?.find((d) => d.domain === "dasha");

  return (
    <div className="dasha-card-section">
      <h2 className="section-title">Current Dasha–Bhukti</h2>

      <div className="prediction-context">
        {currentAge != null && (
          <span className="context-pill">Age {currentAge}</span>
        )}
        {activeDasha && <span className="context-pill">{activeDasha}</span>}
      </div>

      <div className="dasha-card">
        <div className="dasha-card-header">
          <div className="dasha-lords">
            <span className="dasha-lord-chip maha">
              {titleize(maha.lord)} <em>Maha</em>
            </span>
            {bhukti && (
              <span className="dasha-lord-chip bhukti">
                {titleize(bhukti.lord)} <em>Bhukti</em>
              </span>
            )}
          </div>
          <span
            className={`fav-badge ${dasha.favourable ? "fav-yes" : "fav-no"}`}
          >
            {dasha.favourable ? "Favourable" : "Challenging"}
          </span>
        </div>

        <div className="score-row">
          <div className="score-track">
            <div
              className={`score-fill ${scoreClass(score)}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="score-value">
            {score != null ? `${score}/10` : "—"}
          </span>
        </div>

        {dasha.shashtashtaka && (
          <div className="dasha-flag warn">
            ⚠ Maha & Bhukti lords are in a 6–8 (Shashtashtaka) relationship —
            an unfavourable pairing.
          </div>
        )}

        {nar?.narrative && (
          <p className="prediction-narrative">{nar.narrative}</p>
        )}

        {reasons.length > 0 && (
          <div className="dasha-rules">
            <span className="dasha-rules-label">
              Why ({titleize(maha.lord)} Maha)
            </span>
            <ul className="dasha-rules-list">
              {reasons.map((r, i) => (
                <li key={i} className={`rule-${r.verdict.replace("/", "-")}`}>
                  <span className="rule-dot" />
                  {r.text}
                </li>
              ))}
            </ul>
          </div>
        )}

        {narrative?.disclaimer && (
          <p className="prediction-disclaimer">{narrative.disclaimer}</p>
        )}
      </div>
    </div>
  );
};

export default DashaCard;
