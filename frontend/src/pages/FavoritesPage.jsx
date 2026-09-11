import { AnimatePresence, motion } from "framer-motion";
import { useFavorites } from "../hooks/useFavorites";

export default function FavoritesPage() {
  const { status, favorites, error, remove } = useFavorites();

  return (
    <div className="container favorites-page">
      <h1 className="page-heading">Favorites</h1>

      {status === "loading" && <div className="skeleton" style={{ height: 160 }} />}
      {status === "error" && <p className="section-error">{error?.message}</p>}
      {status === "success" && favorites.length === 0 && (
        <p className="chat-empty-sub">No saved cities yet. Save one from the dashboard.</p>
      )}

      <div className="favorites-grid">
        <AnimatePresence>
          {favorites.map((f) => (
            <motion.div
              key={f.id}
              className="favorite-card"
              layout
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.85 }}
              transition={{ duration: 0.4, ease: [0.34, 1.56, 0.64, 1] }}
            >
              <span className="favorite-card-name">{f.name}</span>
              <span className="favorite-card-country">{f.country}</span>
              <button className="favorite-remove" onClick={() => remove(f.id)}>
                Remove
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
