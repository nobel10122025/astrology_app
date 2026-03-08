import React, { useState } from "react";
import ErrorBoundary from "./components/ErrorBoundary/index";
import Header from "./components/Header/index";
import Form from "./components/form/index";
import ResultsDisplay from "./components/ResultsDisplay/index";
import AllDashasPage from "./components/all-dashas-page/index";
import RelationshipPage from "./components/relationship-page/index";
import MarriagePage from "./components/marriage-page/index";
import { useAstrologyForm } from "./hooks/useAstrologyForm";
import { useTheme } from "./hooks/useTheme";
import { useViewControls } from "./hooks/useViewControls";
import "./App.css";

function App() {
  const [currentPage, setCurrentPage] = useState("home");
  
  const { theme, setTheme } = useTheme();
  const {
    formData,
    setFormData,
    loading,
    results,
    error,
    moonDataForDashas,
    handleSubmit,
  } = useAstrologyForm();
  
  const {
    viewMode,
    expandItem,
    activeTab,
    sortOrder,
    setViewMode,
    setActiveTab,
    setSortOrder,
    toggle,
    sortResults,
  } = useViewControls();


  if (currentPage === "all-dashas") {
    return (
      <AllDashasPage
        moonData={moonDataForDashas}
        birthDate={formData.dateOfBirth}
        onBack={() => setCurrentPage("home")}
      />
    );
  }

  if (currentPage === "relationship") {
    return (
      <RelationshipPage
        relationship={results?.relationship}
        onBack={() => setCurrentPage("home")}
      />
    );
  }

  if (currentPage === "marriage") {
    return (
      <MarriagePage
        marriage={results?.marriage}
        onBack={() => setCurrentPage("home")}
      />
    );
  }

  return (
    <ErrorBoundary>
      <div className="App">
        <Header theme={theme} setTheme={setTheme} />
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

          <ResultsDisplay
            results={results}
            viewMode={viewMode}
            activeTab={activeTab}
            expandItem={expandItem}
            toggle={toggle}
            sortResults={sortResults}
            sortOrder={sortOrder}
            setSortOrder={setSortOrder}
            setActiveTab={setActiveTab}
            setViewMode={setViewMode}
            setCurrentPage={setCurrentPage}
          />
        </div>
      </div>
    </ErrorBoundary>
  );
}

export default App;
