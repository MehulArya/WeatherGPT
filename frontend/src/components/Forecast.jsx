import { motion } from "framer-motion";
import { conditionIcon } from "./Icons";

const DAY_FMT = new Intl.DateTimeFormat(undefined, { weekday: "short" });
const DATE_FMT = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" });

function Skeleton() {
  return (
    <div className="strip">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="skeleton strip-card" />
      ))}
    </div>
  );
}

export default function Forecast({ status, data, units, error }) {
  if (status === "idle") return null;
  if (status === "loading") return <Skeleton />;
  if (status === "error") {
    return <p className="section-error">{error?.message || "Couldn't load the forecast."}</p>;
  }

  const maxKey = units === "imperial" ? "temperature_max_f" : "temperature_max_c";
  const minKey = units === "imperial" ? "temperature_min_c" && "temperature_min_f" : "temperature_min_c";
  const unitSymbol = units === "imperial" ? "°" : "°";

  return (
    <div className="strip" role="list">
      {data.daily.map((day, i) => {
        const Icon = conditionIcon(day.condition);
        const date = new Date(day.date + "T00:00:00");
        return (
          <motion.div
            key={day.date}
            role="listitem"
            className="strip-card"
            initial={{ clipPath: "inset(0 0 100% 0)" }}
            animate={{ clipPath: "inset(0 0 0% 0)" }}
            transition={{ duration: 0.5, delay: i * 0.05, ease: [0.16, 1, 0.3, 1] }}
          >
            <span className="strip-day">{i === 0 ? "Today" : DAY_FMT.format(date)}</span>
            <span className="strip-date">{DATE_FMT.format(date)}</span>
            <Icon size={20} />
            <span className="strip-temp tabular">
              {Math.round(day[maxKey])}
              {unitSymbol}
              <span className="strip-temp-min"> / {Math.round(day[units === "imperial" ? "temperature_min_f" : "temperature_min_c"])}{unitSymbol}</span>
            </span>
            <span className="strip-precip tabular">{day.precipitation_probability_pct}% rain</span>
          </motion.div>
        );
      })}
    </div>
  );
}
