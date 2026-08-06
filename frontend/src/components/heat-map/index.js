import React from 'react';

import { PLANET_SYMBOLS, HOUSE_SYMBOLS } from '../../utils/constants';
import { getValue } from '../../utils/basic-logic';

import './style.css';

const HeatMap = ({ results, handleClick, is_planet_heatmap }) => {
  return (
    <div className="heatmap-container">
    {results.map((item, index) => {
  // Planets AND houses now tint by their net contact balance (subathuvam +
  // papathuvam) on the point-scale; fall back to legacy final_score if absent.
  let hue, intensity, display;
  if (item.net_contact !== undefined) {
    const net = getValue(item.net_contact);
    hue = net > 0 ? 120 : net < 0 ? 0 : 60;
    intensity = (Math.min(Math.abs(net), 200) / 200) * 100;
    display = `${net > 0 ? "+" : ""}${net}`;
  } else {
    const legacy = getValue(item.final_score);
    intensity = ((legacy + 5) / 20) * 100;
    hue = legacy >= 7 ? 120 : legacy >= 5 ? 60 : 0;
    display = legacy.toFixed(1);
  }
  const symbol = is_planet_heatmap ? PLANET_SYMBOLS[item.planet.toUpperCase()] : HOUSE_SYMBOLS[item.rasi.toUpperCase()];

  return (
    <div
      key={index}
      className="heatmap-cell"
      style={{
        backgroundColor: `hsl(${hue}, 70%, ${100 - intensity/2}%)`,
        transform: `scale(${0.8 + intensity/200})`
      }}
      onClick={() => handleClick(item)}
    >
      <div className="planet-symbol-large">{symbol || '●'}</div>
      <div className="planet-name-small">{is_planet_heatmap ? item.planet : item.rasi} {!is_planet_heatmap &&  `(House ${item.house})`}</div>
      <div className="planet-score-heatmap">{display}</div>
    </div>
  );
    })}
  </div>
  );
};

export default HeatMap;