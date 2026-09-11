import { motion } from "framer-motion";
import AnimatedNumber from "./AnimatedNumber";
import { conditionIcon } from "./Icons";

function Skeleton() {
  return (
    <div className="hero-weather">
      <div className="skeleton" style={{ width: "60%", height: "var(--type-hero)", marginBottom: 8 }} />
      <div className="skeleton" style={{ width: "40%", height: 24 }} />
    </div>
  );
}

export default function CurrentWeather({ status, data, units, error }) {
  if (status === "idle") {
    return (
      <div className="hero-weather hero-weather--empty">
        <p className="hero-empty-text">Search a city to see current conditions here.</p>
      </div>
    );
  }

  if (status === "loading") return <Skeleton />;

  if (status === "error") {
    return (
      <div className="hero-weather hero-weather--error">
        <p>{error?.message || "Couldn't load current conditions."}</p>
      </div>
    );
  }

  const { location, current } = data;
  const temp = units === "imperial" ? current.temperature_f : current.temperature_c;
  const feels = units === "imperial" ? current.feels_like_f : current.feels_like_c;
  const wind = units === "imperial" ? current.wind_mph : current.wind_kmh;
  const precip = units === "imperial" ? current.precipitation_in : current.precipitation_mm;
  const unitSymbol = units === "imperial" ? "°F" : "°C";
  const windUnit = units === "imperial" ? "mph" : "km/h";
  const precipUnit = units === "imperial" ? "in" : "mm";
  const Icon = conditionIcon(current.condition);

  return (
    <motion.div
      className="hero-weather"
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.65, 0, 0.35, 1] }}
    >
      <div className="hero-weather-top">
        <span className="hero-location">{location.name}</span>
        <span className="hero-condition">
          <Icon size={18} />
          {current.condition}
        </span>
      </div>

      <div className="hero-temp">
        <AnimatedNumber value={temp} decimals={0} />
        <span className="hero-temp-unit">{unitSymbol}</span>
      </div>

      <div className="hero-readout">
        <div className="hero-readout-item">
          <span className="hero-readout-label">Feels like</span>
          <span className="tabular">
            <AnimatedNumber value={feels} decimals={0} />
            {unitSymbol}
          </span>
        </div>
        <div className="hero-readout-item">
          <span className="hero-readout-label">Humidity</span>
          <span className="tabular">
            <AnimatedNumber value={current.humidity_pct} decimals={0} />%
          </span>
        </div>
        <div className="hero-readout-item">
          <span className="hero-readout-label">Wind</span>
          <span className="tabular">
            <AnimatedNumber value={wind} decimals={0} /> {windUnit}
          </span>
        </div>
        <div className="hero-readout-item">
          <span className="hero-readout-label">Precipitation</span>
          <span className="tabular">
            <AnimatedNumber value={precip} decimals={1} /> {precipUnit}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
