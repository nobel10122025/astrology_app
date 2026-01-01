import React from "react";

import { getValue, getReason } from '../../utils/basic-logic';

const CardDetailRow = ({label, item, colorClass = ""}) => {
  const value = getValue(item);
  const reason = getReason(item);

  // Handle arrays (like planets_list) - should not happen in breakdown, but safety check
  if (Array.isArray(value)) {
    return (
      <div className="detail-row">
        <span>{label}:</span>
        <span
          className={`value ${colorClass} ${reason ? "has-tooltip" : ""}`}
          style={{ cursor: reason ? "help" : "default" }}
        >
          {value.length}
          {reason && <span className="tooltip">{reason}</span>}
        </span>
      </div>
    );
  }

  // Ensure value is a primitive (number or string)
  const numValue = typeof value === "number" ? value : 0;
  const displayValue = numValue > 0 ? `+${numValue}` : numValue;

  return (
    <div className="detail-row">
      <span>{label}:</span>
      <span
        className={`value ${colorClass} ${reason ? "has-tooltip" : ""}`}
        style={{ cursor: reason ? "help" : "default" }}
      >
        {displayValue}
        {reason && <span className="tooltip">{reason}</span>}
      </span>
    </div>
  );
};

export default CardDetailRow;
