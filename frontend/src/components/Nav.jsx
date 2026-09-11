import { motion } from "framer-motion";

const NAV_ITEMS = [
  { key: "dashboard", label: "Dashboard" },
  { key: "compare", label: "Compare" },
  { key: "conversations", label: "Conversations" },
  { key: "favorites", label: "Favorites" },
];

export default function Nav({ page, onNavigate, units, onToggleUnits, theme, onToggleTheme }) {
  return (
    <header className="nav">
      <div className="container nav-row">
        <button className="wordmark" onClick={() => onNavigate("dashboard")} aria-label="WeatherGPT home">
          <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="4.2" fill="none" stroke="var(--accent-500)" strokeWidth="1.6" />
            <line x1="12" y1="2.5" x2="12" y2="5.5" stroke="var(--accent-500)" strokeWidth="1.6" />
            <line x1="12" y1="18.5" x2="12" y2="21.5" stroke="var(--accent-500)" strokeWidth="1.6" />
            <line x1="2.5" y1="12" x2="5.5" y2="12" stroke="var(--accent-500)" strokeWidth="1.6" />
            <line x1="18.5" y1="12" x2="21.5" y2="12" stroke="var(--accent-500)" strokeWidth="1.6" />
          </svg>
          <span>WeatherGPT</span>
        </button>

        <nav className="nav-links" aria-label="Primary">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              className={`nav-link ${page === item.key ? "is-active" : ""}`}
              onClick={() => onNavigate(item.key)}
            >
              {item.label}
              {page === item.key && (
                <motion.span layoutId="nav-underline" className="nav-underline" transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }} />
              )}
            </button>
          ))}
        </nav>

        <div className="nav-controls">
          <button
            className="theme-toggle"
            onClick={onToggleTheme}
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            title={theme === "dark" ? "Light mode" : "Dark mode"}
          >
            {theme === "dark" ? "☾" : "☀"}
          </button>
          <button className="unit-toggle" onClick={onToggleUnits} aria-label="Toggle temperature units">
            <span className={units === "metric" ? "is-active" : ""}>°C</span>
            <span className="unit-toggle-divider">/</span>
            <span className={units === "imperial" ? "is-active" : ""}>°F</span>
          </button>
        </div>
      </div>
    </header>
  );
}
