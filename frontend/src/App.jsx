import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Nav from "./components/Nav";
import Dashboard from "./pages/Dashboard";
import ComparePage from "./pages/ComparePage";
import ConversationsPage from "./pages/ConversationsPage";
import FavoritesPage from "./pages/FavoritesPage";

const PAGES = {
  dashboard: Dashboard,
  compare: ComparePage,
  conversations: ConversationsPage,
  favorites: FavoritesPage,
};

function GrainOverlay() {
  return (
    <svg className="grain" aria-hidden="true">
      <filter id="grain-filter">
        <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" />
        <feColorMatrix type="saturate" values="0" />
      </filter>
      <rect width="100%" height="100%" filter="url(#grain-filter)" />
    </svg>
  );
}

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [units, setUnits] = useState("metric");
  const [theme, setTheme] = useState(() => localStorage.getItem("weathergpt_theme") || "dark");

  // Keep <html data-theme> in sync so <body> (and everything outside
  // .app-shell) inherits the semantic tokens -- this is what makes the
  // entire page background actually switch between dark and light.
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const toggleTheme = () =>
    setTheme((t) => {
      const next = t === "dark" ? "light" : "dark";
      localStorage.setItem("weathergpt_theme", next);
      return next;
    });

  const Page = PAGES[page] || Dashboard;

  return (
    <div data-theme={theme} className="app-shell">
      <GrainOverlay />
      <Nav page={page} onNavigate={setPage} units={units} onToggleUnits={() => setUnits((u) => (u === "metric" ? "imperial" : "metric"))} theme={theme} onToggleTheme={toggleTheme} />
      <main>
        <AnimatePresence mode="wait">
          <motion.div
            key={page}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.5, ease: [0.65, 0, 0.35, 1] }}
          >
            <Page units={units} />
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
