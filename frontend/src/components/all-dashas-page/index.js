import React, { useState, useEffect } from "react";
import "./style.css";

const AllDashasPage = ({ moonData, birthDate, onBack }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [allDashasData, setAllDashasData] = useState(null);
  const [expandedDasha, setExpandedDasha] = useState(null);
  const [expandedAntardasha, setExpandedAntardasha] = useState(null);

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

  useEffect(() => {
    if (moonData && birthDate) {
      fetchAllDashas();
    }
  }, [moonData, birthDate]);

  const fetchAllDashas = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:5001/api/all-dashas", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          moon: moonData,
          birth_date: birthDate,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || "Failed to fetch all dashas");
      }

      const data = await response.json();
      if (data.status === "success" && data.data) {
        setAllDashasData(data.data);
      } else {
        throw new Error("Invalid response format");
      }
    } catch (err) {
      setError(err.message || "An error occurred while fetching dashas");
      console.error("Error:", err);
    } finally {
      setLoading(false);
    }
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
    
    let result = `${wholeYears} year${wholeYears !== 1 ? "s" : ""}`;
    if (months > 0) {
      result += ` ${months} month${months > 1 ? "s" : ""}`;
    }
    return result;
  };

  const toggleDasha = (index) => {
    setExpandedDasha(expandedDasha === index ? null : index);
    setExpandedAntardasha(null);
  };

  const toggleAntardasha = (dashaIndex, antardashaIndex) => {
    const key = `${dashaIndex}-${antardashaIndex}`;
    setExpandedAntardasha(expandedAntardasha === key ? null : key);
  };

  if (loading) {
    return (
      <div className="all-dashas-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading all dashas...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="all-dashas-page">
        <div className="error-container">
          <p className="error-message">Error: {error}</p>
          <button className="back-button" onClick={onBack}>
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (!allDashasData) {
    return (
      <div className="all-dashas-page">
        <div className="error-container">
          <p className="error-message">No data available</p>
          <button className="back-button" onClick={onBack}>
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="all-dashas-page">
      <div className="all-dashas-header">
        <button className="back-button" onClick={onBack}>
          ← Back to Home
        </button>
        <h1 className="page-title">All Dashas (120 Years)</h1>
        <div className="birth-info">
          <p>
            <strong>Birth Date:</strong> {allDashasData.birth_date}
          </p>
          <p>
            <strong>Birth Nakshatra:</strong> {allDashasData.birth_nakshatra}
          </p>
          <p>
            <strong>Birth Dasha Lord:</strong>{" "}
            {planetNames[allDashasData.birth_dasha_lord] ||
              allDashasData.birth_dasha_lord.toUpperCase()}
          </p>
        </div>
      </div>

      <div className="dashas-container">
        {allDashasData.dashas && allDashasData.dashas.length > 0 ? (
          allDashasData.dashas.map((dasha, dashaIndex) => (
            <div key={dashaIndex} className="dasha-card">
              <div
                className="dasha-header"
                onClick={() => toggleDasha(dashaIndex)}
              >
                <div className="dasha-header-left">
                  <span className="dasha-number">{dashaIndex + 1}</span>
                  <span className="dasha-lord-name">
                    {planetNames[dasha.lord] || dasha.lord.toUpperCase()}
                  </span>
                </div>
                <div className="dasha-header-right">
                  <span className="dasha-period">
                    {formatYears(dasha.period_years)}
                  </span>
                  <span className="expand-icon">
                    {expandedDasha === dashaIndex ? "▼" : "▶"}
                  </span>
                </div>
              </div>
              <div className="dasha-dates">
                <span className="date-label">Start:</span>
                <span className="date-value">{dasha.start_date}</span>
                <span className="date-label">End:</span>
                <span className="date-value">{dasha.end_date}</span>
              </div>

              {expandedDasha === dashaIndex && (
                <div className="antardashas-container">
                  <h4 className="antardashas-title">Antardashas</h4>
                  {dasha.antardashas && dasha.antardashas.length > 0 ? (
                    dasha.antardashas.map((antardasha, antardashaIndex) => {
                      const antardashaKey = `${dashaIndex}-${antardashaIndex}`;
                      return (
                        <div
                          key={antardashaIndex}
                          className="antardasha-item"
                        >
                          <div
                            className="antardasha-header"
                            onClick={() =>
                              toggleAntardasha(dashaIndex, antardashaIndex)
                            }
                          >
                            <div className="antardasha-header-left">
                              <span className="antardasha-number">
                                {antardashaIndex + 1}
                              </span>
                              <span className="antardasha-lord-name">
                                {planetNames[antardasha.lord] ||
                                  antardasha.lord.toUpperCase()}
                              </span>
                            </div>
                            <div className="antardasha-header-right">
                              <span className="antardasha-period">
                                {formatYears(antardasha.period_years)}
                              </span>
                              <span className="expand-icon">
                                {expandedAntardasha === antardashaKey
                                  ? "▼"
                                  : "▶"}
                              </span>
                            </div>
                          </div>
                          <div className="antardasha-dates">
                            <span className="date-label">Start:</span>
                            <span className="date-value">
                              {antardasha.start_date}
                            </span>
                            <span className="date-label">End:</span>
                            <span className="date-value">
                              {antardasha.end_date}
                            </span>
                          </div>

                          {expandedAntardasha === antardashaKey && (
                            <div className="pratyantardashas-container">
                              <h5 className="pratyantardashas-title">
                                Pratyantardashas
                              </h5>
                              {antardasha.pratyantardashas &&
                              antardasha.pratyantardashas.length > 0 ? (
                                antardasha.pratyantardashas.map(
                                  (pratyantar, pratyantarIndex) => (
                                    <div
                                      key={pratyantarIndex}
                                      className="pratyantar-item"
                                    >
                                      <div className="pratyantar-header">
                                        <span className="pratyantar-number">
                                          {pratyantarIndex + 1}
                                        </span>
                                        <span className="pratyantar-lord-name">
                                          {planetNames[pratyantar.lord] ||
                                            pratyantar.lord.toUpperCase()}
                                        </span>
                                        <span className="pratyantar-period">
                                          {formatYears(pratyantar.period_years)}
                                        </span>
                                      </div>
                                      <div className="pratyantar-dates">
                                        <span className="date-label">Start:</span>
                                        <span className="date-value">
                                          {pratyantar.start_date}
                                        </span>
                                        <span className="date-label">End:</span>
                                        <span className="date-value">
                                          {pratyantar.end_date}
                                        </span>
                                      </div>
                                    </div>
                                  )
                                )
                              ) : (
                                <p className="no-data">
                                  No pratyantardashas available
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })
                  ) : (
                    <p className="no-data">No antardashas available</p>
                  )}
                </div>
              )}
            </div>
          ))
        ) : (
          <p className="no-data">No dashas data available</p>
        )}
      </div>
    </div>
  );
};

export default AllDashasPage;

