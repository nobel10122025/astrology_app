import { useState } from 'react';

export const useViewControls = () => {
  const [viewMode, setViewMode] = useState("cards");
  const [expandItem, setExpandItem] = useState(new Set());
  const [activeTab, setActiveTab] = useState("planets");
  const [sortOrder, setSortOrder] = useState("current");

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

  const sortResults = (resultsArray) => {
    if (!resultsArray || !Array.isArray(resultsArray)) {
      return resultsArray;
    }

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
        return sorted;
    }
  };

  return {
    viewMode,
    setViewMode,
    expandItem,
    activeTab,
    setActiveTab,
    sortOrder,
    setSortOrder,
    toggle,
    sortResults,
  };
};
