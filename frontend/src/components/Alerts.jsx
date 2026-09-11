import { motion } from "framer-motion";

function Skeleton() {
  return <div className="skeleton" style={{ height: 72, marginBottom: 8 }} />;
}

export default function Alerts({ status, data, error }) {
  if (status === "idle") return null;
  if (status === "loading") return <Skeleton />;
  if (status === "error") {
    return <p className="section-error">{error?.message || "Couldn't load alerts."}</p>;
  }

  if (!data || data.length === 0) {
    return <p className="alerts-empty">No advisories for this location right now.</p>;
  }

  return (
    <div>
      {data.map((alert, i) => (
        <motion.div
          key={alert.id}
          className={`alert-card alert-card--${alert.severity}`}
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] }}
        >
          <div className="alert-card-head">
            <span className="alert-type">{alert.alert_type}</span>
            <span className={`alert-severity alert-severity--${alert.severity}`}>{alert.severity}</span>
          </div>
          <p className="alert-title">{alert.title}</p>
          <p className="alert-description">{alert.description}</p>
          <p className="alert-advice">{alert.advice}</p>
        </motion.div>
      ))}
      <p className="alerts-disclaimer">General guidance — not an official meteorological warning.</p>
    </div>
  );
}
