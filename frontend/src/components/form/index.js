import React from "react";
import "./style.css";

const Form = ({ formData, setFormData, handleSubmit, loading }) => {

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="planetary-form">
      {/* Personal Information */}
      <div className="form-section">
        <h2>Personal Information</h2>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="name">Name:</label>
            <input
              type="text"
              id="name"
              value={formData.name || ""}
              onChange={(e) => handleInputChange("name", e.target.value)}
              placeholder="Enter name"
              required
            />
          </div>
        </div>
      </div>

      {/* Date and Time of Birth */}
      <div className="form-section">
        <h2>Date & Time of Birth</h2>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="dateOfBirth">Date of Birth:</label>
            <input
              type="date"
              id="dateOfBirth"
              value={formData.dateOfBirth || ""}
              onChange={(e) => handleInputChange("dateOfBirth", e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="timeOfBirth">Time of Birth:</label>
            <input
              type="time"
              id="timeOfBirth"
              value={formData.timeOfBirth || ""}
              onChange={(e) => handleInputChange("timeOfBirth", e.target.value)}
              required
            />
          </div>
        </div>
      </div>

      {/* Location */}
      <div className="form-section">
        <h2>Location</h2>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="latitude">Latitude:</label>
            <input
              type="number"
              id="latitude"
              min="-90"
              max="90"
              step="0.0001"
              value={formData.latitude || ""}
              onChange={(e) => handleInputChange("latitude", e.target.value)}
              placeholder="Enter latitude (e.g., 10.3624)"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="longitude">Longitude:</label>
            <input
              type="number"
              id="longitude"
              min="-180"
              max="180"
              step="0.0001"
              value={formData.longitude || ""}
              onChange={(e) => handleInputChange("longitude", e.target.value)}
              placeholder="Enter longitude (e.g., 77.9695)"
              required
            />
          </div>
        </div>
      </div>

      {/* 6 Degree Correction */}
      <div className="form-section">
        <div className="form-row">
          <div className="form-group checkbox-group">
            <label htmlFor="sixDegreeCorrection" className="checkbox-label">
              <input
                type="checkbox"
                id="sixDegreeCorrection"
                checked={formData.sixDegreeCorrection || false}
                onChange={(e) => handleInputChange("sixDegreeCorrection", e.target.checked)}
              />
              <span>6 Degree Correction</span>
            </label>
          </div>
        </div>
      </div>

      <button type="submit" className="submit-button" disabled={loading}>
        {loading ? "Calculating..." : "Calculate"}
      </button>
    </form>
  );
};

export default Form;
