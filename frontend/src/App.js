import React, { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { setProfile } from "./store/user/actions";

import HeatMap from "./components/heat-map/index";
import CardContent from "./components/card-content/index";
import Form from "./components/form/index";
import TableContent from "./components/table-content/index";
import ProfessionPrediction from "./components/profession-prediction/index";
import DashaDisplay from "./components/dasha-display/index";
import AllDashasPage from "./components/all-dashas-page/index";

import { SIGN_MAP, PLANET_SYMBOLS } from "./utils/constants";
import { capitalizeFirstLetter } from "./utils/basic-logic";
import { themes } from "./utils/theme-constants";

import "./App.css";

function App() {
  // Initialize form state
  const dispatch = useDispatch();
  const profile = useSelector((state) => state.user.profile);
  const [formData, setFormData] = useState({
    name: "",
    dateOfBirth: "",
    timeOfBirth: "",
    latitude: "",
    longitude: "",
    sixDegreeCorrection: false,
  });

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState("cards"); // 'cards', 'table', 'heatmap'
  const [expandItem, setExpandItem] = useState(new Set());
  const [activeTab, setActiveTab] = useState("planets"); // 'planets' or 'houses'
  const [sortOrder, setSortOrder] = useState("current"); // 'current', 'score-low-high', 'score-high-low'
  const [theme, setTheme] = useState("default"); // 'default', 'lightBlue', 'lightGreen'
  const [currentPage, setCurrentPage] = useState("home"); // 'home' or 'all-dashas'
  const [moonDataForDashas, setMoonDataForDashas] = useState(null); // Store moon data for all-dashas page

  // Apply theme to document root
  useEffect(() => {
    const currentTheme = themes[theme];
    if (currentTheme) {
      document.documentElement.style.setProperty('--theme-bg-gradient', currentTheme.bgGradient);
      document.documentElement.style.setProperty('--theme-header-bg', currentTheme.headerBg);
      document.documentElement.style.setProperty('--theme-primary', currentTheme.primaryColor);
      document.documentElement.style.setProperty('--theme-secondary', currentTheme.secondaryColor);
      document.documentElement.setAttribute('data-theme', theme);
    }
  }, [theme]);

  const toggle = (item) => {
    setExpandItem((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(item)) {
        newSet.delete(item);
      } else {
        newSet.add(item);
      }
      return newSet;
    });
  };

  // Sort results based on sortOrder
  const sortResults = (resultsArray) => {
    if (!resultsArray || !Array.isArray(resultsArray)) {
      return resultsArray;
    }

    // Create a copy to avoid mutating the original array
    const sorted = [...resultsArray];

    switch (sortOrder) {
      case "score-low-high":
        return sorted.sort((a, b) => {
          const scoreA = a.final_score || 0;
          const scoreB = b.final_score || 0;
          return scoreA - scoreB;
        });
      case "score-high-low":
        return sorted.sort((a, b) => {
          const scoreA = a.final_score || 0;
          const scoreB = b.final_score || 0;
          return scoreB - scoreA;
        });
      case "current":
      default:
        return sorted; // Return in original order
    }
  };

  // Map sign number (1-12) to rasi name
  const getRasiName = (signNumber) => {
    return SIGN_MAP[signNumber] || "";
  };

  // Get previous sign number (wraps around from 1 to 12)
  const getPreviousSign = (signNumber) => {
    if (signNumber <= 1) {
      return 12; // Wrap around: 1 -> 12
    }
    return signNumber - 1;
  };

  // Transform astrology API response to backend format
  const transformAstrologyResponse = (apiResponse, applyCorrection = false) => {
    // The API response has output array with two objects
    // We'll use the second one which has planet names as keys
    const planetData =
      apiResponse.output && apiResponse.output[1] ? apiResponse.output[1] : {};

    const transformed = {};
    const correction = applyCorrection ? 6 : 0;

    // Transform Ascendant
    if (planetData.Ascendant) {
      const asc = planetData.Ascendant;
      const normDegree = parseFloat(asc.normDegree);
      const currentSign = asc.current_sign;
      
      // Validate: normDegree must be a valid number, currentSign must be a number between 1-12
      if (!isNaN(normDegree) && typeof currentSign === 'number' && currentSign >= 1 && currentSign <= 12) {
        let correctedDegree = normDegree - correction;
        let correctedSign = currentSign;

      // If degree becomes negative, move to previous rasi
      if (correctedDegree < 0) {
        correctedSign = getPreviousSign(asc.current_sign);
        correctedDegree = 30 + correctedDegree; // e.g., -1 becomes 29
      }

        transformed.ascendant = {
          degree: Math.max(0, Math.min(30, correctedDegree)).toString(), // Ensure degree is between 0-30
          house: getRasiName(correctedSign),
        };
      }
    }

    Object.keys(PLANET_SYMBOLS).forEach((apiName) => {
      const backendName = capitalizeFirstLetter(apiName.toLowerCase());
      if (planetData[backendName]) {
        const planet = planetData[backendName];
        const normDegree = parseFloat(planet.normDegree);
        const currentSign = planet.current_sign;
        
        // Validate: normDegree must be a valid number, currentSign must be a number between 1-12
        if (!isNaN(normDegree) && typeof currentSign === 'number' && currentSign >= 1 && currentSign <= 12) {
          let correctedDegree = normDegree - correction;
          let correctedSign = currentSign;

          // If degree becomes negative, move to previous rasi
          if (correctedDegree < 0) {
            correctedSign = getPreviousSign(currentSign);
            correctedDegree = 30 + correctedDegree; // e.g., -1 becomes 29
          }

        transformed[apiName.toLowerCase()] = {
          degree: correctedDegree.toString(),
          house: getRasiName(correctedSign),
        };
      }
    }});

    return transformed;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      // Parse date and time
      const dateObj = new Date(formData.dateOfBirth);
      const [hours, minutes] = formData.timeOfBirth.split(":");
      const year = dateObj.getFullYear();
      const month = dateObj.getMonth() + 1; // JavaScript months are 0-indexed
      const date = dateObj.getDate();

      // Calculate timezone offset (default to IST: +5:30)
      const timezoneOffset = new Date().getTimezoneOffset();
      const timezone = -(timezoneOffset / 60); // Convert to hours
      dispatch(setProfile({
        name: formData.name,
        dateOfBirth: formData.dateOfBirth,
        timeOfBirth: formData.timeOfBirth,
        latitude: formData.latitude,
        longitude: formData.longitude,
      }));

      // Prepare request payload for astrology API
      const astrologyPayload = {
        year: year,
        month: month,
        date: date,
        hours: parseInt(hours, 10),
        minutes: parseInt(minutes, 10),
        seconds: 0,
        latitude: parseFloat(formData.latitude),
        longitude: parseFloat(formData.longitude),
        timezone: timezone,
        settings: {
          observation_point: "geocentric",
          ayanamsha: "lahiri",
        },
      };

      // Call astrology API
      const apiKey = process.env.REACT_APP_ASTROLOGY_API_KEY;
      if (!apiKey) {
        throw new Error("ASTROLOGY_API_KEY environment variable is not set");
      }

      const astrologyResponse = await fetch(
        "https://json.freeastrologyapi.com/planets",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "x-api-key": apiKey,
          },
          body: JSON.stringify(astrologyPayload),
        }
      );

      if (!astrologyResponse.ok) {
        const errorData = await astrologyResponse.json().catch(() => ({}));
        throw new Error(
          errorData.message ||
            `Astrology API error: ${astrologyResponse.status}`
        );
      }

      const astrologyData = await astrologyResponse.json();

      // Transform the response to backend format (apply 6-degree correction if checkbox is checked)
      const transformedData = transformAstrologyResponse(
        astrologyData,
        formData.sixDegreeCorrection || false
      );

      // Validate that all required fields are present and valid
      const requiredFields = ['ascendant', 'sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu'];
      const missingFields = requiredFields.filter(field => {
        const fieldData = transformedData[field];
        return !fieldData || !fieldData.degree || !fieldData.house;
      });

      if (missingFields.length > 0) {
        throw new Error(`Missing or invalid data for: ${missingFields.join(', ')}`);
      }

      // Call backend with transformed data (without birth_date for main calculation)
      const calculatePayload = { ...transformedData };
      const backendResponse = await fetch(
        "http://localhost:5001/api/calculate",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(calculatePayload),
        }
      );

      const backendData = await backendResponse.json();
      if (!backendResponse.ok) {
        throw new Error(backendData.error || "Failed to calculate");
      }

      // Call dasha-info endpoint separately
      let dashaData = null;
      if (transformedData.moon && transformedData.moon.house && transformedData.moon.degree) {
        try {
          const dashaPayload = {
            moon: transformedData.moon,
            birth_date: formData.dateOfBirth
          };
          const dashaResponse = await fetch(
            "http://localhost:5001/api/dasha-info",
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify(dashaPayload),
            }
          );

          if (dashaResponse.ok) {
            const dashaResponseData = await dashaResponse.json();
            if (dashaResponseData.status === 'success' && dashaResponseData.dasha) {
              dashaData = dashaResponseData.dasha;
            }
          }
        } catch (dashaErr) {
          // Log error but don't fail the entire request
          console.warn("Failed to fetch dasha info:", dashaErr);
        }
      }

      // Merge dasha data into results
      const finalResults = {
        ...backendData,
        ...(dashaData && { dasha: dashaData })
      };
      setResults(finalResults);
      
      // Store moon data for all-dashas page
      if (transformedData.moon) {
        setMoonDataForDashas(transformedData.moon);
      }
    } catch (err) {
      setError(err.message || "An error occurred while calculating");
      console.error("Error:", err);
    } finally {
      setLoading(false);
    }
  };

  // If on all-dashas page, render that component
  if (currentPage === "all-dashas") {
    return (
      <AllDashasPage
        moonData={moonDataForDashas}
        birthDate={formData.dateOfBirth}
        onBack={() => setCurrentPage("home")}
      />
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <div className="header-title">
            <h1>Subathuvam Pavathuvam</h1>
            <p>Planetary Position Form</p>
          </div>
          <div className="theme-selector">
            <label htmlFor="theme-select">Theme:</label>
            <select
              id="theme-select"
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
              className="theme-select"
            >
              {Object.keys(themes).map((themeKey) => (
                <option key={themeKey} value={themeKey}>
                  {themes[themeKey].name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </header>
      <div className="form-container">
        <Form
          formData={formData}
          setFormData={setFormData}
          handleSubmit={handleSubmit}
          loading={loading}
        />
        {error && (
          <div className="error-message">
            <p>Error: {error}</p>
          </div>
        )}

        {results && results.status === "success" && (
          <div className="results-container">
            <h2>Calculation Results</h2>

            {/* Rasi Chart */}
            {results.chart_html && (
              <div
                className="chart-wrapper"
                dangerouslySetInnerHTML={{ __html: results.chart_html }}
              />
            )}

            <div className="summary">
              <p>
                <strong>Total Planets:</strong> {results.summary.total_planets}
              </p>
              <p>
                <strong>Average Planet Score:</strong>{" "}
                {results.summary.average_score}
              </p>
              {results.summary.total_houses && (
                <>
                  <p>
                    <strong>Total Houses:</strong>{" "}
                    {results.summary.total_houses}
                  </p>
                  <p>
                    <strong>Average House Score:</strong>{" "}
                    {results.summary.average_house_score}
                  </p>
                </>
              )}
            </div>

            {/* Tab Toggle */}
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

            {/* Sort Dropdown */}
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

            {/* View Mode Toggle */}
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

            {/* Planets Section */}
            {activeTab === "planets" && (
              <>
                {/* Cards View */}
                {viewMode === "cards" && (
                  <CardContent
                    results={sortResults(results.results)}
                    expandItem={expandItem}
                    toggle={toggle}
                    is_planet_card={true}
                  />
                )}

                {/* Heat Map View */}
                {viewMode === "heatmap" && (
                  <HeatMap
                    results={sortResults(results.results)}
                    handleClick={() => {}}
                    is_planet_heatmap={true}
                  />
                )}

                {/* Table View */}
                {viewMode === "table" && (
                  <TableContent
                    results={sortResults(results.results)}
                    is_planet_table={true}
                  />
                )}
              </>
            )}

            {/* Houses Section */}
            {activeTab === "houses" && results.house_results && (
              <>
                {/* Cards View */}
                {viewMode === "cards" && (
                  <CardContent
                    results={sortResults(results.house_results)}
                    expandItem={expandItem}
                    toggle={toggle}
                    is_planet_card={false}
                  />
                )}

                {/* Heat Map View */}
                {viewMode === "heatmap" && (
                  <HeatMap
                    results={sortResults(results.house_results)}
                    handleClick={() => {}}
                    is_planet_heatmap={false}
                  />
                )}

                {/* Table View */}
                {viewMode === "table" && (
                  <TableContent
                    results={sortResults(results.house_results)}
                    is_planet_table={false}
                  />
                )}
              </>
            )}

            {/* Dasha & Antardasha Section */}
            {results.dasha && (
              <>
                <DashaDisplay dasha={results.dasha} />
                <div className="view-all-dashas-button-container">
                  <button
                    className="view-all-dashas-button"
                    onClick={() => setCurrentPage("all-dashas")}
                  >
                    View all dashas
                  </button>
                </div>
              </>
            )}

            {/* Profession Prediction Section */}
            {results.prediction && results.prediction.profession && (
              <ProfessionPrediction
                profession={results.prediction.profession}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
