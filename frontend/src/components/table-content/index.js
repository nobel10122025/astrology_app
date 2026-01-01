import React from "react";

//utils
import { getValue, getReason } from "../../utils/basic-logic";
import { planetTableHeaders, houseTableHeaders } from "./utils";

import "./style.css";

const TableContent = ({ results, is_planet_table }) => {
    const tableHeaders = is_planet_table ? planetTableHeaders : houseTableHeaders;

    const getClassName = (row, header) => {
        const { positive, negative, key } = header;
        if (positive && negative) {
            if (row[key] > 5) {
                return "positive";
            } else if (row[key] < 5) {
                return "negative";
            }
        } else if (positive) {
            return "positive";
        } else if (negative) {
            return "negative";
        }
        return "normal";
    }
  return (
    <div className="table-wrapper">
      <table className="results-table">
        <thead>
          <tr>
            {tableHeaders.map((header) => (
                <th key={header.key}>{header.label}</th>
            ))}
            </tr>
        </thead>
        <tbody>
          {results.map((row, index) => {
            return (
            <tr key={index}>
              {tableHeaders.map((header) => (
                <td key={header.key} title={getReason(row[header.key])} className={getClassName(row, header)}>{getValue(row[header.key])}</td>
              ))}
            </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default TableContent;