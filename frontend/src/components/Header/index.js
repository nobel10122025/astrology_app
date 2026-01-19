import React from 'react';
import { themes } from '../../utils/theme-constants';
import './Header.css';

const Header = ({ theme, setTheme }) => {
  return (
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
  );
};

export default Header;
