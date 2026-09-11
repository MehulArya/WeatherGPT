import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { compareCities } from "../api/weather";
import { conditionIcon } from "../components/Icons";
import AnimatedNumber from "../components/AnimatedNumber";

function CityColumn({ side, cityData, units }) {
  if (!cityData) {
    return (
      <div className="compare-column compare-column--empty">
        <p>Enter a city to compare.</p>
      </div>
    );
  }
  const { location, current } = cityData;
  const temp = units === "imperial" ? current.temperature_f : current.temperature_c;
  const unitSymbol = units === "imperial" ? "°F" : "°C";
  const Icon = conditionIcon(current.condition);

  return (
    <motion.div
      className="compare-column"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      <span className="compare-city-name">{location.name}</span>
      <div className="compare-temp">
        <AnimatedNumber value={temp} decimals={0} />
        <span className="compare-temp-unit">{unitSymbol}</span>
      </div>
      <span className="compare-condition">
        <Icon size={18} /> {current.condition}
      </span>
      <dl className="compare-stats">
        <div>
          <dt>Feels like</dt>
          <dd className="tabular">
            {units === "imperial" ? current.feels_like_f : current.feels_like_c}
            {unitSymbol}
          </dd>
        </div>
        <div>
          <dt>Humidity</dt>
          <dd className="tabular">{current.humidity_pct}%</dd>
        </div>
        <div>
          <dt>Wind</dt>
          <dd className="tabular">
            {units === "imperial" ? current.wind_mph : current.wind_kmh}{" "}
            {units === "imperial" ? "mph" : "km/h"}
          </dd>
        </div>
      </dl>
    </motion.div>
  );
}

export default function ComparePage({ units }) {
  const [city1, setCity1] = useState("Jaipur");
  const [city2, setCity2] = useState("Delhi");
  const [status, setStatus] = useState("idle");
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  async function handleCompare(e) {
    e.preventDefault();
    setStatus("loading");
    setError(null);
    try {
      const res = await compareCities(city1, city2, units);
      setData(res);
      setStatus("success");
    } catch (err) {
      setError(err);
      setStatus("error");
    }
  }

  useEffect(() => {
    if (data) handleCompare({ preventDefault() {} });
  }, [units]); // eslint-disable-line react-hooks/exhaustive-deps

  const a = data?.comparison?.[0];
  const b = data?.comparison?.[1];
  let leadLine = "";
  if (a && b) {
    const tempKey = units === "imperial" ? "temperature_f" : "temperature_c";
    const windKey = units === "imperial" ? "wind_mph" : "wind_kmh";
    const warmer = a.current[tempKey] > b.current[tempKey] ? a.location.name : b.location.name;
    const windier = a.current[windKey] > b.current[windKey] ? a.location.name : b.location.name;
    leadLine = `${warmer} is warmer right now; ${windier} is windier.`;
  }

  return (
    <div className="container compare-page">
      <h1 className="page-heading">Compare two cities</h1>
      <form className="compare-form" onSubmit={handleCompare}>
        <input value={city1} onChange={(e) => setCity1(e.target.value)} placeholder="First city" />
        <span className="compare-form-divider" aria-hidden="true" />
        <input value={city2} onChange={(e) => setCity2(e.target.value)} placeholder="Second city" />
        <button type="submit" disabled={status === "loading"}>
          {status === "loading" ? "Comparing…" : "Compare"}
        </button>
      </form>

      {status === "error" && <p className="section-error">{error?.message}</p>}
      {leadLine && <p className="compare-lead">{leadLine}</p>}

      <div className="compare-grid">
        <CityColumn side="a" cityData={a} units={units} />
        <div className="compare-divider" aria-hidden="true" />
        <CityColumn side="b" cityData={b} units={units} />
      </div>
    </div>
  );
}
