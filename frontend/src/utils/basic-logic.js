const getValue = (item) => {
  // Handle null/undefined
  if (item === null || item === undefined) {
    return 0;
  }
  // Handle arrays (don't treat as value objects)
  if (Array.isArray(item)) {
    return item;
  }
  // Handle objects with value property
  if (typeof item === "object" && "value" in item) {
    return item.value;
  }
  // Return primitive values as-is
  return item;
};

const getReason = (item) => {
  // Handle null/undefined
  if (item === null || item === undefined) {
    return "";
  }
  // Handle arrays (no reason)
  if (Array.isArray(item)) {
    return "";
  }
  // Handle objects with reason property
  if (typeof item === "object" && "reason" in item) {
    return item.reason;
  }
  return "";
};

const getScoreColor = (score) => {
  if (score >= 7) return '#28a745';
  if (score >= 5) return '#ffc107';
  return '#dc3545';
};

function capitalizeFirstLetter(word) {
  if (!word) {
    return ""; // Handle empty string input
  }
  // Get the first character and capitalize it, then add the rest of the string
  return word.charAt(0).toUpperCase() + word.slice(1);
}
export { getValue, getReason, getScoreColor, capitalizeFirstLetter };
