import { useState } from 'react';

export const useViewControls = () => {
  const [viewMode, setViewMode] = useState("cards");
  const [expandItem, setExpandItem] = useState(new Set());
  const [activeTab, setActiveTab] = useState("planets");
  // Default: surface planets that carry BOTH a benefic and a malefic contact.
  const [sortOrder, setSortOrder] = useState("both-first");

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

  // --- new two-track accessors (planet items carry `tracks`; houses don't) ---
  const t1 = (x) => x?.tracks?.subathuvam_papathuvam;
  const track1 = (x) => t1(x)?.value ?? x?.final_score ?? 0;   // net (tiebreak)
  const subathuvam = (x) => t1(x)?.subathuvam ?? 0;            // benefic sum >= 0
  const papathuvam = (x) => Math.abs(t1(x)?.papathuvam ?? 0);  // malefic magnitude
  const track2 = (x) => x?.tracks?.dig_sthana?.value ?? 0;

  // How many "sides" a planet has in Track 1: 0 = both benefic & malefic,
  // 1 = only one side, 2 = neither. Used to float "both" planets to the top.
  const effectRank = (x) => {
    const hasPos = subathuvam(x) > 0;
    const hasNeg = papathuvam(x) > 0;
    if (hasPos && hasNeg) return 0;
    if (hasPos || hasNeg) return 1;
    return 2;
  };

  const sortResults = (resultsArray) => {
    if (!resultsArray || !Array.isArray(resultsArray)) {
      return resultsArray;
    }

    const sorted = [...resultsArray];

    switch (sortOrder) {
      // planets that have BOTH subathuvam and papathuvam first, then by the
      // stronger net Track-1 balance within each group.
      case "both-first":
        return sorted.sort(
          (a, b) => effectRank(a) - effectRank(b) || track1(b) - track1(a)
        );
      case "subathuvam-high-low":
        return sorted.sort((a, b) => subathuvam(b) - subathuvam(a));
      case "subathuvam-low-high":
        return sorted.sort((a, b) => subathuvam(a) - subathuvam(b));
      case "papathuvam-high-low":
        return sorted.sort((a, b) => papathuvam(b) - papathuvam(a));
      case "papathuvam-low-high":
        return sorted.sort((a, b) => papathuvam(a) - papathuvam(b));
      case "sthana-high-low":
        return sorted.sort((a, b) => track2(b) - track2(a));
      case "sthana-low-high":
        return sorted.sort((a, b) => track2(a) - track2(b));
      case "score-low-high":
        return sorted.sort((a, b) => (a.final_score || 0) - (b.final_score || 0));
      case "score-high-low":
        return sorted.sort((a, b) => (b.final_score || 0) - (a.final_score || 0));
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
