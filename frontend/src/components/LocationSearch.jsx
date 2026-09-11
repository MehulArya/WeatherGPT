import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { searchLocation } from "../api/weather";

export default function LocationSearch({ onSelect }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const timer = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await searchLocation(query, 5);
        setResults(res.results || []);
        setOpen(true);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 320);
    return () => clearTimeout(timer.current);
  }, [query]);

  useEffect(() => {
    function handleClick(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function handleSelect(loc) {
    onSelect(loc);
    setQuery(loc.name);
    setOpen(false);
  }

  return (
    <div className="location-search" ref={containerRef}>
      <label htmlFor="city-search" className="location-search-label">
        Search a city
      </label>
      <input
        id="city-search"
        className="location-search-input"
        type="text"
        placeholder="Jaipur, Delhi, Tokyo…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results.length && setOpen(true)}
        autoComplete="off"
      />
      <span className="location-search-underline" />

      <AnimatePresence>
        {open && (query.trim().length > 0) && (
          <motion.ul
            className="location-search-results"
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
          >
            {loading && <li className="location-search-empty">Searching…</li>}
            {!loading && results.length === 0 && (
              <li className="location-search-empty">No matches. Try another spelling.</li>
            )}
            {!loading &&
              results.map((r) => (
                <li key={`${r.name}-${r.latitude}`}>
                  <button onClick={() => handleSelect(r)}>
                    <span>{r.name}</span>
                    <span className="location-search-country">{r.country}</span>
                  </button>
                </li>
              ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}
