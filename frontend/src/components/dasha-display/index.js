import React, { useState } from "react";
import "./style.css";

const DashaDisplay = ({ dasha }) => {
  const [selectedAntardasha, setSelectedAntardasha] = useState(null);
  const [showModal, setShowModal] = useState(false);

  if (!dasha || !dasha.dasha) {
    return null;
  }

  const { dasha: dashaInfo, current_antardasha, all_antardashas } = dasha;

  // Planet name mapping
  const planetNames = {
    ketu: "Ketu",
    venus: "Venus",
    sun: "Sun",
    moon: "Moon",
    mars: "Mars",
    rahu: "Rahu",
    jupiter: "Jupiter",
    saturn: "Saturn",
    mercury: "Mercury",
  };

  const formatYears = (years) => {
    if (years < 1) {
      const months = Math.floor(years * 12);
      const days = Math.floor((years * 365.25) % 30);
      if (months > 0) {
        return `${months} month${months > 1 ? "s" : ""} ${days} day${days !== 1 ? "s" : ""}`;
      }
      return `${days} day${days !== 1 ? "s" : ""}`;
    }
    const wholeYears = Math.floor(years);
    const months = Math.floor((years - wholeYears) * 12);
    const days = Math.floor(((years - wholeYears) * 365.25) % 30);
    
    let result = `${wholeYears} year${wholeYears !== 1 ? "s" : ""}`;
    if (months > 0) {
      result += ` ${months} month${months > 1 ? "s" : ""}`;
    }
    if (days > 0 && wholeYears < 2) {
      result += ` ${days} day${days !== 1 ? "s" : ""}`;
    }
    return result;
  };

  const handleAntardashaClick = (antardasha) => {
    setSelectedAntardasha(antardasha);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedAntardasha(null);
  };

  return (
    <div className="dasha-display-section">
      <h2 className="section-title">Dasha & Antardasha</h2>
      <div className="dasha-card">
        <div className="dasha-card-header">
          <div className="dasha-icon">🌙</div>
          <h3 className="dasha-card-title">Current Dasha Period</h3>
        </div>
        <div className="dasha-card-content">
          <div className="dasha-info-row">
            <span className="dasha-label">Current Dasha Lord:</span>
            <span className="dasha-value dasha-lord">
              {planetNames[dashaInfo.lord] || dashaInfo.lord.toUpperCase()}
            </span>
          </div>
          {dashaInfo.birth_dasha_lord && dashaInfo.birth_dasha_lord !== dashaInfo.lord && (
            <div className="dasha-info-row">
              <span className="dasha-label">Birth Dasha Lord:</span>
              <span className="dasha-value">
                {planetNames[dashaInfo.birth_dasha_lord] || dashaInfo.birth_dasha_lord.toUpperCase()}
              </span>
            </div>
          )}
          <div className="dasha-info-row">
            <span className="dasha-label">Nakshatra (at Birth):</span>
            <span className="dasha-value">{dashaInfo.nakshatra}</span>
          </div>
          {dashaInfo.elapsed_years !== undefined && (
            <div className="dasha-info-row">
              <span className="dasha-label">Elapsed in Current Dasha:</span>
              <span className="dasha-value">
                {formatYears(dashaInfo.elapsed_years)}
              </span>
            </div>
          )}
          <div className="dasha-info-row">
            <span className="dasha-label">Remaining Period:</span>
            <span className="dasha-value dasha-period">
              {formatYears(dashaInfo.remaining_years)}
            </span>
          </div>
          {dashaInfo.start_date && (
            <div className="dasha-info-row">
              <span className="dasha-label">Start Date:</span>
              <span className="dasha-value">{dashaInfo.start_date}</span>
            </div>
          )}
          {dashaInfo.end_date && (
            <div className="dasha-info-row">
              <span className="dasha-label">End Date:</span>
              <span className="dasha-value">{dashaInfo.end_date}</span>
            </div>
          )}
        </div>

        {current_antardasha && (
          <div className="antardasha-section">
            <h4 className="antardasha-title">Current Antardasha</h4>
            <div 
              className="dasha-card-content antardasha-clickable"
              onClick={() => handleAntardashaClick(current_antardasha)}
              style={{ cursor: 'pointer' }}
            >
              <div className="dasha-info-row">
                <span className="dasha-label">Antardasha Lord:</span>
                <span className="dasha-value dasha-lord">
                  {planetNames[current_antardasha.lord] || current_antardasha.lord.toUpperCase()}
                </span>
              </div>
              <div className="dasha-info-row">
                <span className="dasha-label">Period:</span>
                <span className="dasha-value">
                  {formatYears(current_antardasha.period_years)}
                </span>
              </div>
              {current_antardasha.start_date && (
                <div className="dasha-info-row">
                  <span className="dasha-label">Start Date:</span>
                  <span className="dasha-value">{current_antardasha.start_date}</span>
                </div>
              )}
              {current_antardasha.end_date && (
                <div className="dasha-info-row">
                  <span className="dasha-label">End Date:</span>
                  <span className="dasha-value">{current_antardasha.end_date}</span>
                </div>
              )}
              {current_antardasha.pratyantardashas && current_antardasha.pratyantardashas.length > 0 && (
                <div className="dasha-info-row">
                  <span className="dasha-label">Pratyantar Dashas:</span>
                  <span className="dasha-value" style={{ fontSize: '0.85rem', opacity: 0.9 }}>
                    Click to view ({current_antardasha.pratyantardashas.length})
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {all_antardashas && all_antardashas.length > 0 && (
          <div className="all-antardashas-section">
            <h4 className="antardasha-title">All Antardashas in Current Dasha</h4>
            <div className="antardasha-list">
              {all_antardashas.map((antardasha, index) => (
                <div
                  key={index}
                  className={`antardasha-item ${
                    current_antardasha &&
                    current_antardasha.lord === antardasha.lord
                      ? "active"
                      : ""
                  }`}
                  onClick={() => handleAntardashaClick(antardasha)}
                  style={{ cursor: 'pointer' }}
                >
                  <div className="antardasha-main">
                    <span className="antardasha-lord">
                      {planetNames[antardasha.lord] || antardasha.lord.toUpperCase()}
                    </span>
                    <span className="antardasha-period">
                      {formatYears(antardasha.period_years)}
                    </span>
                  </div>
                  {antardasha.start_date && antardasha.end_date && (
                    <div className="antardasha-dates-small">
                      <div className="antardasha-date-row">
                        <span className="antardasha-date-label">Start:</span>
                        <span className="antardasha-date-value">{antardasha.start_date}</span>
                      </div>
                      <div className="antardasha-date-row">
                        <span className="antardasha-date-label">End:</span>
                        <span className="antardasha-date-value">{antardasha.end_date}</span>
                      </div>
                    </div>
                  )}
                  {antardasha.pratyantardashas && antardasha.pratyantardashas.length > 0 && (
                    <div className="antardasha-pratyantar-hint">
                      Click to view Pratyantar Dashas ({antardasha.pratyantardashas.length})
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="dasha-card-footer">
          <p className="dasha-note">
            Based on Vimshottari Dasha system calculated from Moon's nakshatra position
          </p>
        </div>
      </div>

      {/* Pratyantar Dasha Modal */}
      {showModal && selectedAntardasha && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">
                Pratyantar Dashas - {planetNames[selectedAntardasha.lord] || selectedAntardasha.lord.toUpperCase()}
              </h3>
              <button className="modal-close" onClick={closeModal}>×</button>
            </div>
            <div className="modal-body">
              <div className="antardasha-info-summary">
                <div className="summary-row">
                  <span className="summary-label">Period:</span>
                  <span className="summary-value">{formatYears(selectedAntardasha.period_years)}</span>
                </div>
                {selectedAntardasha.start_date && selectedAntardasha.end_date && (
                  <>
                    <div className="summary-row">
                      <span className="summary-label">Start Date:</span>
                      <span className="summary-value">{selectedAntardasha.start_date}</span>
                    </div>
                    <div className="summary-row">
                      <span className="summary-label">End Date:</span>
                      <span className="summary-value">{selectedAntardasha.end_date}</span>
                    </div>
                  </>
                )}
              </div>
              {selectedAntardasha.pratyantardashas && selectedAntardasha.pratyantardashas.length > 0 ? (
                <div className="pratyantar-list">
                  {selectedAntardasha.pratyantardashas.map((pratyantar, index) => (
                    <div key={index} className="pratyantar-item">
                      <div className="pratyantar-header">
                        <span className="pratyantar-lord">
                          {planetNames[pratyantar.lord] || pratyantar.lord.toUpperCase()}
                        </span>
                        <span className="pratyantar-period">
                          {formatYears(pratyantar.period_years)}
                        </span>
                      </div>
                      <div className="pratyantar-dates">
                        <div className="pratyantar-date-row">
                          <span className="pratyantar-date-label">Start:</span>
                          <span className="pratyantar-date-value">{pratyantar.start_date}</span>
                        </div>
                        <div className="pratyantar-date-row">
                          <span className="pratyantar-date-label">End:</span>
                          <span className="pratyantar-date-value">{pratyantar.end_date}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-pratyantar">
                  <p>No pratyantar dashas available for this antardasha.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashaDisplay;

