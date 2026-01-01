import React from "react";
import "./style.css";

const ProfessionPrediction = ({ profession }) => {
  if (!profession) {
    return null;
  }

  let planetsNames = [];
  let professions = [];
  let errorMessage = null;

  // Handle JSON object format
  if (typeof profession === "object" && profession !== null) {
    // Check if it's already in the correct format
    if (profession.planets && profession.professions) {
      planetsNames =
        Array.isArray(profession.planets) && profession.planets.length > 0
          ? profession.planets.map((planet) =>
              typeof planet === "string" ? planet.toUpperCase() : String(planet).toUpperCase()
            )
          : [];
      professions =
        Array.isArray(profession.professions) && profession.professions.length > 0
          ? profession.professions
          : [];
      
      // Check for error
      if (profession.error) {
        errorMessage = profession.error;
      }
    }
  } else if (typeof profession === "string") {
    // Try to parse JSON string (fallback for old format)
    try {
      const parsed = JSON.parse(profession);
      if (parsed.planets && parsed.professions) {
        planetsNames =
          Array.isArray(parsed.planets) && parsed.planets.length > 0
            ? parsed.planets.map((planet) =>
                typeof planet === "string" ? planet.toUpperCase() : String(planet).toUpperCase()
              )
            : [];
        professions =
          Array.isArray(parsed.professions) && parsed.professions.length > 0
            ? parsed.professions
            : [];
      }
    } catch (e) {
      // If parsing fails, treat as plain text (old format)
      const parts = profession.split(":");
      const planetName = parts[0]?.trim() || "";
      const professionList = parts[1]?.trim() || profession;
      
      if (planetName) {
        planetsNames = [planetName.toUpperCase()];
      }
      if (professionList) {
        professions = professionList.split(",").map((p) => p.trim()).filter((p) => p);
      }
    }
  }

  // Don't render if no data
  if (planetsNames.length === 0 && professions.length === 0 && !errorMessage) {
    return null;
  }

  return (
    <div className="profession-prediction-section">
      <h2 className="section-title">Profession Prediction</h2>
      <div className="profession-card">
        <div className="profession-card-header">
          <div className="profession-icon">💼</div>
          <h3 className="profession-card-title">Career Guidance</h3>
        </div>
        <div className="profession-card-content">
          {planetsNames.length > 0 && (
            <div className="planet-indicator">
              <span className="planet-label">
                Influencing Planet{planetsNames.length > 1 ? "s" : ""}:
              </span>
              <span className="planet-name-profession">{planetsNames.join(", ")}</span>
            </div>
          )}
          <div className="profession-text">
            {errorMessage ? (
              <p className="profession-error">Error: {errorMessage}</p>
            ) : professions.length > 0 ? (
              <div>
                <p className="profession-description">
                  {professions.map((prof, index) => (
                    <span key={index} className="profession-item">
                      {prof}
                      {index < professions.length - 1 && ", "}
                    </span>
                  ))}
                </p>
              </div>
            ) : (
              <p className="profession-description">No profession recommendations available.</p>
            )}
          </div>
        </div>
        <div className="profession-card-footer">
          <p className="profession-note">
            Based on Vedic astrology analysis of planetary positions, house
            connectivity, and subathuva calculations
          </p>
        </div>
      </div>
    </div>
  );
};

export default ProfessionPrediction;

