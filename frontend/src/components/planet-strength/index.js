import React, { useState } from "react";
import "./style.css";

const titleize = (s) =>
  (s || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

const sentenceCase = (s) =>
  s ? s.charAt(0).toUpperCase() + s.slice(1) : s;

// Track scores run 0..10 with 5 as neutral.
const trackClass = (score) => {
  if (score == null) return "trk-unknown";
  if (score >= 6.5) return "trk-high";
  if (score >= 4.0) return "trk-mid";
  return "trk-low";
};

const VERDICT_CLASS = {
  "strongly favourable": "verdict-strong-good",
  favourable: "verdict-good",
  mixed: "verdict-mixed",
  unfavourable: "verdict-bad",
  "strongly unfavourable": "verdict-strong-bad",
};

const ROLE_LABELS = {
  maha: "Maha lord",
  bhukti: "Bhukti lord",
  natal: "Natal",
};

const TRACK_META = {
  bala: { label: "Bala", hint: "intrinsic capacity — can it act?" },
  sambandha: { label: "Sambandha", hint: "contact quality — who touches it?" },
  adhikara: { label: "Adhikara", hint: "lordship — what does it govern?" },
};

const DELIVERS_LABELS = {
  good: "Delivers the good significations",
  bad: "Delivers the damaged significations",
  mixed: "Delivers mixed significations",
  "n/a": "Owns no house (judge by dispositor)",
};

const TrackMeter = ({ name, track }) => {
  const meta = TRACK_META[name] || { label: titleize(name), hint: "" };
  const score = track?.score;
  const pct = score != null ? (score / 10) * 100 : 0;
  return (
    <div className="ps-track">
      <div className="ps-track-head">
        <span className="ps-track-name">{meta.label}</span>
        <span className="ps-track-score">{score != null ? score : "—"}</span>
      </div>
      <div className="ps-track-bar">
        <div
          className={`ps-track-fill ${trackClass(score)}`}
          style={{ width: `${pct}%` }}
        />
        <span className="ps-track-neutral" />
      </div>
      <div className="ps-track-hint">{meta.hint}</div>
    </div>
  );
};

const PlanetCard = ({ planet, packet, judgement }) => {
  const [open, setOpen] = useState(false);
  const placement = packet.placement || {};
  const tracks = packet.tracks || {};
  const delivers = packet.delivers || {};
  const conflicts = packet.conflicts || [];

  const verdict = judgement?.verdict;
  const facts = [
    ...(tracks.bala?.facts || []),
    ...(tracks.sambandha?.facts || []),
    ...(tracks.adhikara?.facts || []),
  ];
  const citedSet = new Set(judgement?.cited || []);

  return (
    <div className="ps-card">
      <div className="ps-card-header">
        <div className="ps-card-title-wrap">
          <h3 className="ps-card-title">{titleize(planet)}</h3>
          {packet.role && (
            <span className="ps-role">{ROLE_LABELS[packet.role] || packet.role}</span>
          )}
        </div>
        {verdict && (
          <span className={`ps-verdict ${VERDICT_CLASS[verdict] || ""}`}>
            {titleize(verdict)}
          </span>
        )}
      </div>

      <div className="ps-placement">
        {placement.house_name && (
          <span>
            {placement.house != null && `${placement.house}th house`}
            {placement.house_name && ` · ${placement.house_name}`}
          </span>
        )}
        {placement.rasi && <span>{titleize(placement.rasi)}</span>}
        {placement.degree_in_sign != null && (
          <span>{placement.degree_in_sign}°</span>
        )}
        {placement.dispositor && (
          <span>disp. {titleize(placement.dispositor)}</span>
        )}
      </div>

      <div className="ps-tracks">
        <TrackMeter name="bala" track={tracks.bala} />
        <TrackMeter name="sambandha" track={tracks.sambandha} />
        <TrackMeter name="adhikara" track={tracks.adhikara} />
      </div>

      {judgement?.reasoning && (
        <p className="ps-reasoning">{judgement.reasoning}</p>
      )}

      {judgement?.dominant_track && (
        <div className="ps-dominant">
          Decided by <strong>{TRACK_META[judgement.dominant_track]?.label ||
            titleize(judgement.dominant_track)}</strong>
          {judgement.source === "fallback" && (
            <span className="ps-fallback"> · deterministic (no LLM)</span>
          )}
        </div>
      )}

      {(delivers.significations?.length > 0 || judgement?.delivers?.length > 0) && (
        <div className="ps-delivers">
          <span className="ps-delivers-label ps-side-good">
            {DELIVERS_LABELS[delivers.side] || "Delivers"}
          </span>
          <div className="ps-chip-row">
            {(judgement?.delivers?.length ? judgement.delivers : delivers.significations)
              .slice(0, 10)
              .map((s, i) => (
                <span className="ps-chip ps-chip-good" key={`d-${i}`}>
                  {sentenceCase(s)}
                </span>
              ))}
          </div>
        </div>
      )}

      {judgement?.withholds?.length > 0 && (
        <div className="ps-delivers">
          <span className="ps-delivers-label ps-side-bad">Withholds / damages</span>
          <div className="ps-chip-row">
            {judgement.withholds.slice(0, 10).map((s, i) => (
              <span className="ps-chip ps-chip-bad" key={`w-${i}`}>
                {sentenceCase(s)}
              </span>
            ))}
          </div>
        </div>
      )}

      {conflicts.length > 0 && (
        <ul className="ps-conflicts">
          {conflicts.map((c, i) => (
            <li key={i}>
              <span className="ps-conflict-type">{titleize(c.type)}</span>
              {c.note}
            </li>
          ))}
        </ul>
      )}

      <button className="ps-evidence-toggle" onClick={() => setOpen((o) => !o)}>
        {open ? "Hide evidence" : `Show evidence (${facts.length} facts)`}
      </button>

      {open && (
        <ul className="ps-facts">
          {facts.map((f) => (
            <li
              key={f.id}
              className={`ps-fact ps-fact-${f.polarity} ${
                citedSet.has(f.id) ? "ps-fact-cited" : ""
              }`}
            >
              <span className="ps-fact-id">{f.id}</span>
              <span className="ps-fact-note">{f.note}</span>
              {citedSet.has(f.id) && <span className="ps-fact-badge">cited</span>}
            </li>
          ))}
        </ul>
      )}

      {packet.node_rules_pending && (
        <div className="ps-node-note">
          Node — dedicated rule set not yet specified; judge by dispositor and occupancy.
        </div>
      )}
    </div>
  );
};

const TithiSheet = ({ tithi }) => {
  if (!tithi) return null;
  return (
    <div className={`ps-tithi ps-tithi-${tithi.band}`}>
      <div className="ps-tithi-main">
        <span className="ps-tithi-name">{titleize(tithi.tithi_name)}</span>
        <span className="ps-tithi-band">{titleize(tithi.band)} Moon</span>
      </div>
      <div className="ps-tithi-stats">
        <span>Illumination {Math.round((tithi.illumination || 0) * 100)}%</span>
        <span>{tithi.can_aspect ? "Casts aspect" : "No aspect (dark)"}</span>
        {tithi.is_full_moon && <span className="ps-tithi-full">Full Moon</span>}
      </div>
      {tithi.note?.[tithi.band] && (
        <p className="ps-tithi-desc">{tithi.note[tithi.band]}</p>
      )}
    </div>
  );
};

const PlanetStrength = ({ planetStrength }) => {
  const packets = planetStrength?.packets;
  if (
    !planetStrength ||
    planetStrength.status !== "success" ||
    !packets ||
    Object.keys(packets).length === 0
  ) {
    return null;
  }

  const judgements = planetStrength.judgements || {};

  return (
    <div className="ps-section">
      <h2 className="ps-section-title">Three-Track Planet Strength</h2>
      <p className="ps-section-sub">
        Bala, sambandha and adhikara are kept apart — the contradiction between
        them is the reading. Where they conflict, the judge decides which wins.
      </p>

      <div className="ps-context">
        {planetStrength.current_age != null && (
          <span className="ps-pill">Age {planetStrength.current_age}</span>
        )}
        {planetStrength.active_dasha && (
          <span className="ps-pill">{planetStrength.active_dasha}</span>
        )}
      </div>

      <TithiSheet tithi={planetStrength.tithi} />

      <div className="ps-grid">
        {Object.entries(packets).map(([planet, packet]) => (
          <PlanetCard
            key={planet}
            planet={planet}
            packet={packet}
            judgement={judgements[planet]}
          />
        ))}
      </div>
    </div>
  );
};

export default PlanetStrength;
