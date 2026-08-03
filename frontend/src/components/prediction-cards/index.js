import React from "react";
import "./style.css";

const titleize = (s) =>
  (s || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

// Capitalize only the first letter, preserving acronyms like ISRO / NASA.
const sentenceCase = (s) =>
  s ? s.charAt(0).toUpperCase() + s.slice(1) : s;

const TIMING_LABELS = {
  ACTIVE: "Active now",
  UPCOMING: "Coming up",
  PAST: "Already passed",
  GENERAL: "Ongoing tendency",
};

const scoreClass = (score) => {
  if (score == null) return "score-unknown";
  if (score >= 6.5) return "score-high";
  if (score >= 4.5) return "score-mid";
  return "score-low";
};

// How a planet touches a house, in plain words.
const LINK_VERBS = { OCCUPIES: "sits in", OWNS: "rules", ASPECTS: "aspects" };

// House labels for the domains we currently surface; falls back to an ordinal.
const HOUSE_LABELS = {
  2: "2nd house (wealth)",
  10: "10th house (career)",
};

const ordinal = (n) => {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return `${n}${s[(v - 20) % 10] || s[v] || s[0]}`;
};

const houseLabel = (h) => HOUSE_LABELS[h] || `${ordinal(Number(h))} house`;

// Turn { saturn: { "10": ["OCCUPIES","OWNS"] } } into readable evidence lines:
// { planet: "saturn", text: "sits in & rules the 10th house (career)" }
const describeConnections = (conns) =>
  Object.entries(conns || {}).map(([planet, houses]) => {
    const parts = Object.entries(houses).map(([h, kinds]) => {
      const verbs = kinds.map((k) => LINK_VERBS[k] || k.toLowerCase()).join(" & ");
      return `${verbs} the ${houseLabel(h)}`;
    });
    return { planet, text: parts.join(", ") };
  });

const PredictionCards = ({ predictions }) => {
  const domains = predictions?.reading?.domains;
  if (!predictions || !Array.isArray(domains) || domains.length === 0) {
    return null;
  }

  const narrative = predictions.narrative || null;
  // Map domain -> narrative text (present only when narrate=true was used).
  const narrativeByDomain = {};
  if (narrative && Array.isArray(narrative.domains)) {
    narrative.domains.forEach((d) => {
      narrativeByDomain[d.domain] = d;
    });
  }

  // Agents that were age-gated out (skipped) come back in `results`.
  const skipped = (predictions.results || []).filter((r) => r.skipped);

  return (
    <div className="prediction-section">
      <h2 className="section-title">Life Predictions</h2>

      <div className="prediction-context">
        {predictions.current_age != null && (
          <span className="context-pill">Age {predictions.current_age}</span>
        )}
        {predictions.active_dasha && (
          <span className="context-pill">{predictions.active_dasha}</span>
        )}
      </div>

      {narrative?.opening && (
        <p className="prediction-opening">{narrative.opening}</p>
      )}

      <div className="prediction-grid">
        {domains.map((d) => {
          const nar = narrativeByDomain[d.domain];
          const professions = d.details?.indicated_professions || [];
          const connections = describeConnections(d.details?.career_connections);
          const fields = d.details?.field_profile?.fields || [];
          const influence = d.details?.field_profile?.influence || {};
          const influenceParts = d.details?.field_profile?.influence_parts || {};
          const flags = d.special_flags || [];
          const pct = d.score != null ? Math.round((d.score / 10) * 100) : 0;

          return (
            <div className="prediction-card" key={d.domain}>
              <div className="prediction-card-header">
                <h3 className="prediction-card-title">
                  {titleize(nar?.title || d.domain)}
                </h3>
                <span className={`timing-badge timing-${d.timing}`}>
                  {TIMING_LABELS[d.timing] || d.timing}
                </span>
              </div>

              {(d.age_range || d.dasa_context) && (
                <div className="prediction-timing-line">
                  {d.age_range && <span>{d.age_range}</span>}
                  {d.age_range && d.dasa_context && <span> · </span>}
                  {d.dasa_context && <span>{d.dasa_context}</span>}
                </div>
              )}

              <div className="score-row">
                <div className="score-track">
                  <div
                    className={`score-fill ${scoreClass(d.score)}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className="score-value">
                  {d.score != null ? `${d.score}/10` : "—"}
                </span>
              </div>

              {nar?.narrative && (
                <p className="prediction-narrative">{nar.narrative}</p>
              )}

              {fields.length > 0 && (
                <div className="field-block">
                  <span className="field-label">Likely field</span>
                  <div className="field-primary">{sentenceCase(fields[0].field)}</div>
                  {fields[0].matched?.length > 0 && (
                    <div className="chip-row">
                      {fields[0].matched.map((t) => (
                        <span className="chip chip-tag" key={t}>
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                  {fields.length > 1 && (
                    <div className="field-alts">
                      Also possible:{" "}
                      {fields
                        .slice(1, 3)
                        .map((f) => sentenceCase(f.field))
                        .join(", ")}
                    </div>
                  )}
                </div>
              )}

              {professions.length > 0 && (
                <div className="chip-row">
                  {professions.slice(0, 8).map((p, i) => (
                    <span className="chip" key={i}>
                      {p}
                    </span>
                  ))}
                </div>
              )}

              {connections.length > 0 && (
                <div className="why-block">
                  <span className="why-label">Why</span>
                  <ul className="why-list">
                    {connections.map(({ planet, text }) => (
                      <li key={planet}>
                        <strong>{titleize(planet)}</strong> {text}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {Object.keys(influence).length > 0 && (
                <div className="influence-block">
                  <span className="influence-label">Influence</span>
                  <ul className="influence-list">
                    {Object.entries(influence)
                      .sort((a, b) => b[1] - a[1])
                      .map(([planet, w]) => {
                        const parts = influenceParts[planet] || {};
                        return (
                          <li className="influence-item" key={planet}>
                            <div className="influence-row">
                              <span className="influence-planet">
                                {titleize(planet)}
                              </span>
                              <span className="influence-track">
                                <span
                                  className="influence-fill"
                                  style={{ width: `${(w / 10) * 100}%` }}
                                />
                              </span>
                              <span className="influence-val">{w}</span>
                            </div>
                            {(parts.planet_strength != null ||
                              parts.house_strength != null) && (
                              <div className="influence-parts">
                                planet {parts.planet_strength} · house{" "}
                                {parts.house_strength}
                                {parts.occupied_house != null &&
                                  ` (h${parts.occupied_house})`}
                              </div>
                            )}
                          </li>
                        );
                      })}
                  </ul>
                </div>
              )}

              {flags.length > 0 && (
                <ul className="flag-list">
                  {flags.map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              )}

              {d.confidence != null && (
                <div className="confidence-line">
                  Confidence: {Math.round(d.confidence * 100)}%
                </div>
              )}
            </div>
          );
        })}
      </div>

      {skipped.length > 0 && (
        <div className="skipped-note">
          Not applicable yet:{" "}
          {skipped.map((r, i) => (
            <span key={r.domain}>
              {titleize(r.domain)}
              {i < skipped.length - 1 ? ", " : ""}
            </span>
          ))}
        </div>
      )}

      {narrative?.closing && (
        <p className="prediction-closing">{narrative.closing}</p>
      )}

      {narrative?.disclaimer && (
        <p className="prediction-disclaimer">{narrative.disclaimer}</p>
      )}
    </div>
  );
};

export default PredictionCards;
