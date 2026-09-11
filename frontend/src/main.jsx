import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./styles/global.css";
import "./styles/app.css";

// Apply the saved theme to <html> BEFORE first paint so the page
// background is themed from the start (no white flash, no body defaults).
document.documentElement.setAttribute(
  "data-theme",
  localStorage.getItem("weathergpt_theme") || "dark"
);

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
