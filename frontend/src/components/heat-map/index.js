import React from 'react';

import { PLANET_SYMBOLS, HOUSE_SYMBOLS } from '../../utils/constants';
import { getValue } from '../../utils/basic-logic';

import './style.css';

const HeatMap = ({ results, handleClick, is_planet_heatmap }) => {
  return (
    <div className="heatmap-container">
    {results.map((item, index) => {
  const itemScore = getValue(item.final_score);
  const intensity = ((itemScore + 5) / 20) * 100;
  const hue = itemScore >= 7 ? 120 : itemScore >= 5 ? 60 : 0;
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
      <div className="planet-score-heatmap">{itemScore.toFixed(1)}</div>
    </div>
  );
    })}
  </div>
  );
};

export default HeatMap;