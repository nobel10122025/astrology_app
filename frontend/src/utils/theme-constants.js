// ─────────────────────────────────────────────────────────────────────────
// THEME CONFIG — single source of truth for the app's palette.
// To re-skin the whole app, edit the `default` theme below (or swap in your
// brand colours):
//   primaryColor    = the accent (brass) — buttons, borders, chips, links
//   secondaryColor  = the support hue (teal)
//   bgGradient      = the page background
//   headerBg        = the top header background
// Every component reads these via var(--theme-primary/secondary/bg-gradient/
// header-bg), so changing them here recolours everything. `data-theme` is also
// set on <html> for future light/dark refinement.
// ─────────────────────────────────────────────────────────────────────────
export const themes = {
  // Brass astrolabe on teal — the chosen identity.
  default: {
    name: "Brass & Teal",
    bgGradient: "linear-gradient(135deg, #114d47 0%, #0c2f2c 100%)",
    headerBg: "rgba(10, 38, 37, 0.92)",
    primaryColor: "#8f6a1a",   // brass accent
    secondaryColor: "#2a6f6a", // teal support
  },
  lightBlue: {
    name: "Light Blue",
    bgGradient: "linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)",
    headerBg: "rgba(33, 150, 243, 0.9)",
    primaryColor: "#2196f3",
    secondaryColor: "#64b5f6",
  },
  lightGreen: {
    name: "Light Green",
    bgGradient: "linear-gradient(135deg, #f0faf4 0%, #cdebd8 55%, #9fd3b8 100%)",
    headerBg: "rgba(76, 175, 80, 0.9)",
    primaryColor: "#4caf50",
    secondaryColor: "#81c784",
  },
  lightRed: {
    name: "Light Red",
    bgGradient: "linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%)",
    headerBg: "rgba(255, 99, 71, 0.9)",
    primaryColor: "#f44336",
    secondaryColor: "#ef5350",
  },
  yellow: {
    name: "Yellow",
    bgGradient: "linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%)",
    headerBg: "rgba(255, 215, 0, 0.9)",
    primaryColor: "#ffd700",
    secondaryColor: "#ffe680",
  }
};