import { motion } from "framer-motion";
import LocationSearch from "../components/LocationSearch";
import CurrentWeather from "../components/CurrentWeather";
import Forecast from "../components/Forecast";
import Hourly from "../components/Hourly";
import Alerts from "../components/Alerts";
import ChatWindow from "../components/ChatWindow";
import { useWeather } from "../hooks/useWeather";
import { useChat } from "../hooks/useChat";
import { useFavorites } from "../hooks/useFavorites";

export default function Dashboard({ units }) {
  const weather = useWeather(units);
  const favorites = useFavorites();
  const chat = useChat({
    units: weather.units,
    onLocationResolved: weather.applyFromChat,
  });

  const isFavorite =
    weather.location && favorites.favorites.some((f) => f.name === weather.location.name);

  function toggleFavorite() {
    if (!weather.location) return;
    if (isFavorite) {
      const existing = favorites.favorites.find((f) => f.name === weather.location.name);
      if (existing) favorites.remove(existing.id);
    } else {
      favorites.add({
        name: weather.location.name,
        country: weather.location.country || "",
        latitude: weather.location.latitude,
        longitude: weather.location.longitude,
      });
    }
  }

  return (
    <div className="dashboard">
      <section className="dashboard-hero">
        <div className="container dashboard-hero-grid">
          <div className="dashboard-hero-main">
            <LocationSearch onSelect={weather.setLocation} />
            <CurrentWeather
              status={weather.current.status}
              data={weather.current.data}
              units={weather.units}
              error={weather.current.error}
            />
            {weather.location && (
              <button className="favorite-toggle" onClick={toggleFavorite}>
                {isFavorite ? "Remove from favorites" : "Save to favorites"}
              </button>
            )}
          </div>

          <motion.div
            className="dashboard-hero-chat"
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.15, ease: [0.65, 0, 0.35, 1] }}
          >
            <ChatWindow
              messages={chat.messages}
              onSend={chat.send}
              status={chat.status}
              health={chat.health}
            />
          </motion.div>
        </div>
      </section>

      <section className="dashboard-section">
        <div className="container">
          <h2 className="section-heading">Next 7 days</h2>
          <Forecast
            status={weather.forecast.status}
            data={weather.forecast.data}
            units={weather.units}
            error={weather.forecast.error}
          />
        </div>
      </section>

      <section className="dashboard-section">
        <div className="container">
          <h2 className="section-heading">Next 24 hours</h2>
          <Hourly
            status={weather.hourly.status}
            data={weather.hourly.data}
            units={weather.units}
            error={weather.hourly.error}
          />
        </div>
      </section>

      <section className="dashboard-section">
        <div className="container">
          <h2 className="section-heading">Advisories</h2>
          <Alerts status={weather.alerts.status} data={weather.alerts.data} error={weather.alerts.error} />
        </div>
      </section>
    </div>
  );
}
