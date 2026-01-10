import { useState } from "react";
import "./style.css";

export const DateForm = ({ allDashasData }) => {
    const [dashaInfo, setDashaInfo] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const dateOfBirth = e.target.dateOfBirth.value;
    const allDashas = allDashasData.dashas;
    
    const dateDasha = allDashas.reduce((accumulator ,dasha) => {
      if (dateOfBirth >= dasha.start_date && dateOfBirth <= dasha.end_date) {
        accumulator = dasha
      }
      return accumulator;
    }, {});
    if (!dateDasha) {
        setDashaInfo("No Dasha found");
        return;
    }
    const antardasha = dateDasha.antardashas.reduce((accumulator ,antardasha) => {
        if (dateOfBirth >= antardasha.start_date && dateOfBirth <= antardasha.end_date) {
            accumulator = antardasha
        }
        return accumulator;
      
    }, {});
    if (!antardasha) {
        setDashaInfo("No Antardasha found");
        return;
    }
    const pratyantarDasha = antardasha.pratyantardashas.reduce((accumulator, pratyantarDasha) => {
        if (dateOfBirth >= pratyantarDasha.start_date && dateOfBirth <= pratyantarDasha.end_date) {
            accumulator = pratyantarDasha
        }
        return accumulator;
    }, {});
    if (!pratyantarDasha) {
        setDashaInfo("No Pratyantar Dasha found");
        return;
    }
    setDashaInfo(`${dateDasha.lord} - ${antardasha.lord} - ${pratyantarDasha.lord}`)
  };

  return (
    <div className="date-form">
    <form onSubmit={handleSubmit}>
      <div className="form-section">
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="dateOfBirth">Date:</label>
            <input
              type="date"
              id="dateOfBirth"
              required
            />
          </div>
        </div>
        <button type="submit" className="submit-button">Submit</button>
        {dashaInfo && <div className="dasha-info">{dashaInfo}</div>}
      </div>
    </form>
    </div>
  );
};
