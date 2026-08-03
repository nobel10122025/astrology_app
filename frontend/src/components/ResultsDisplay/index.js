import React from 'react';
import CardContent from '../card-content/index';
import TableContent from '../table-content/index';
import HeatMap from '../heat-map/index';
// Career / Life Predictions temporarily disabled:
// import ProfessionPrediction from '../profession-prediction/index';
// import PredictionCards from '../prediction-cards/index';
// Planet-strength panel temporarily disabled (endpoint being made accurate):
// import PlanetStrength from '../planet-strength/index';
import DashaCard from '../dasha-card/index';
import DashaDisplay from '../dasha-display/index';
import './ResultsDisplay.css';

const ResultsDisplay = ({ 
  results, 
  viewMode, 
  activeTab, 
  expandItem, 
  toggle, 
  sortResults, 
  sortOrder, 
  setSortOrder, 
  setActiveTab, 
  setViewMode,
  setCurrentPage 
}) => {
  if (!results || results.status !== "success") {
    return null;
  }

  return (
    <div className="results-container">
      <div className="section-head">
        <p className="eyebrow">Graha &amp; bhava strengths</p>
        <h2>Chart analysis</h2>
      </div>

      {results.chart_html && (
        <div
          className="chart-wrapper"
          dangerouslySetInnerHTML={{ __html: results.chart_html }}
        />
      )}

      <div className="summary">
        <div className="stat-tile">
          <span className="stat-label">Planets</span>
          <span className="stat-val">{results.summary.total_planets}</span>
        </div>
        <div className="stat-tile">
          <span className="stat-label">Avg planet score</span>
          <span className="stat-val accent mono">{results.summary.average_score}</span>
        </div>
        {results.summary.total_houses && (
          <>
            <div className="stat-tile">
              <span className="stat-label">Houses</span>
              <span className="stat-val">{results.summary.total_houses}</span>
            </div>
            <div className="stat-tile">
              <span className="stat-label">Avg house score</span>
              <span className="stat-val mono">{results.summary.average_house_score}</span>
            </div>
          </>
        )}
      </div>

      <div className="controls-section">
        <div className="tab-toggle">
          <button
            className={activeTab === "planets" ? "active" : ""}
            onClick={() => setActiveTab("planets")}
          >
            Planets
          </button>
          <button
            className={activeTab === "houses" ? "active" : ""}
            onClick={() => setActiveTab("houses")}
          >
            Houses
          </button>
        </div>

        <div className="sort-container">
          <label htmlFor="sort-select" className="sort-label">
            Sort by:
          </label>
          <select
            id="sort-select"
            className="sort-select"
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value)}
          >
            <option value="current">Current Order</option>
            <option value="score-low-high">Score (Low to High)</option>
            <option value="score-high-low">Score (High to Low)</option>
          </select>
        </div>

        <div className="view-toggle">
          <button
            className={viewMode === "cards" ? "active" : ""}
            onClick={() => setViewMode("cards")}
          >
            Cards
          </button>
          <button
            className={viewMode === "heatmap" ? "active" : ""}
            onClick={() => setViewMode("heatmap")}
          >
            Heat Map
          </button>
          <button
            className={viewMode === "table" ? "active" : ""}
            onClick={() => setViewMode("table")}
          >
            Table
          </button>
        </div>
      </div>

      {activeTab === "planets" && (
        <div className="content-section">
          {viewMode === "cards" && (
            <CardContent
              results={sortResults(results.results)}
              expandItem={expandItem}
              toggle={toggle}
              is_planet_card={true}
            />
          )}

          {viewMode === "heatmap" && (
            <HeatMap
              results={sortResults(results.results)}
              handleClick={() => {}}
              is_planet_heatmap={true}
            />
          )}

          {viewMode === "table" && (
            <TableContent
              results={sortResults(results.results)}
              is_planet_table={true}
            />
          )}
        </div>
      )}

      {activeTab === "houses" && results.house_results && (
        <div className="content-section">
          {viewMode === "cards" && (
            <CardContent
              results={sortResults(results.house_results)}
              expandItem={expandItem}
              toggle={toggle}
              is_planet_card={false}
            />
          )}

          {viewMode === "heatmap" && (
            <HeatMap
              results={sortResults(results.house_results)}
              handleClick={() => {}}
              is_planet_heatmap={false}
            />
          )}

          {viewMode === "table" && (
            <TableContent
              results={sortResults(results.house_results)}
              is_planet_table={false}
            />
          )}
        </div>
      )}

      {results.dasha && (
        <div className="dasha-section">
          <DashaDisplay dasha={results.dasha} />
          <div className="view-all-dashas-button-container">
            <button
              className="view-all-dashas-button"
              onClick={() => setCurrentPage("all-dashas")}
            >
              View all dashas
            </button>
          </div>
        </div>
      )}

      {results.relationship && (
        <div className="dasha-section">
          <div className="view-all-dashas-button-container">
            <button
              className="view-all-dashas-button"
              onClick={() => setCurrentPage("relationship")}
            >
              View Relationship Analysis
            </button>
          </div>
        </div>
      )}

      {results.marriage && (
        <div className="dasha-section">
          <div className="view-all-dashas-button-container">
            <button
              className="view-all-dashas-button"
              onClick={() => setCurrentPage("marriage")}
            >
              View Marriage Analysis
            </button>
          </div>
        </div>
      )}

      {results.dashaFavourability?.dasha?.available && (
        <DashaCard
          dasha={results.dashaFavourability.dasha}
          narrative={results.dashaFavourability.narrative}
          currentAge={results.dashaFavourability.current_age}
          activeDasha={results.dashaFavourability.active_dasha}
        />
      )}

      {/* Career / Life Predictions temporarily disabled
      {results.predictions && (
        <PredictionCards predictions={results.predictions} />
      )}
      */}

      {/* Planet-strength panel temporarily disabled (endpoint being made accurate)
      {results.planetStrength && (
        <PlanetStrength planetStrength={results.planetStrength} />
      )}
      */}

      {/* Career / Profession Prediction temporarily disabled
      {results.prediction && results.prediction.profession && (
        <ProfessionPrediction
          profession={results.prediction.profession}
        />
      )}
      */}
    </div>
  );
};

export default ResultsDisplay;
