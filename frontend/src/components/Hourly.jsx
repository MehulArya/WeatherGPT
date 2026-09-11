import { motion } from "framer-motion";
import { conditionIcon } from "./Icons";

const HOUR_FMT = new Intl.DateTimeFormat(undefined, { hour: "numeric" });

function Skeleton() {
  return (
    <div className="strip strip--hourly">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="skeleton strip-card strip-card--hourly" />
      ))}
    </div>
  );
}

export default function Hourly({ status, data, units, error }) {
  if (status === "idle") return null;
  if (status === "loading") return <Skeleton />;
  if (status === "error") {
    return <p className="section-error">{error?.message || "Couldn't load the hourly outlook."}</p>;
  }

  const tempKey = units === "imperial" ? "temperature_f" : "temperature_c";

  return (
    <div className="strip strip--hourly" role="list">
      {data.hourly.map((hour, i) => {
        const Icon = conditionIcon(hour.condition);
        const t = new Date(hour.time);
        return (
          <motion.div
            key={hour.time}
            role="listitem"
            className="strip-card strip-card--hourly"
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: i * 0.015, ease: [0.16, 1, 0.3, 1] }}
          >
            <span className="strip-day">{i === 0 ? "Now" : HOUR_FMT.format(t)}</span>
            <Icon size={18} />
            <span className="strip-temp tabular">{Math.round(hour[tempKey])}°</span>
            <span className="strip-precip tabular">{hour.precipitation_probability_pct}%</span>
          </motion.div>
        );
      })}
    </div>
  );
}
