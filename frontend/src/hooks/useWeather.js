import { useCallback, useEffect, useState } from "react";
import { getCurrent, getForecast, getHourly } from "../api/weather";
import { getAlertsFor } from "../api/alerts";

const initialSection = { status: "idle", data: null, error: null };

export function useWeather(controlledUnits) {
  const [location, setLocation] = useState(null); // { name, latitude, longitude }
  const [internalUnits, setInternalUnits] = useState("metric");
  const units = controlledUnits || internalUnits;
  const setUnits = setInternalUnits;
  const [current, setCurrent] = useState(initialSection);
  const [forecast, setForecast] = useState(initialSection);
  const [hourly, setHourly] = useState(initialSection);
  const [alerts, setAlerts] = useState(initialSection);

  const loadAll = useCallback(async (loc, u) => {
    if (!loc) return;
    setCurrent({ status: "loading", data: null, error: null });
    setForecast({ status: "loading", data: null, error: null });
    setHourly({ status: "loading", data: null, error: null });
    setAlerts({ status: "loading", data: null, error: null });

    getCurrent(loc.latitude, loc.longitude, u)
      .then((d) => setCurrent({ status: "success", data: d, error: null }))
      .catch((e) => setCurrent({ status: "error", data: null, error: e }));

    getForecast(loc.latitude, loc.longitude, 7, u)
      .then((d) => setForecast({ status: "success", data: d, error: null }))
      .catch((e) => setForecast({ status: "error", data: null, error: e }));

    getHourly(loc.latitude, loc.longitude, 24, u)
      .then((d) => setHourly({ status: "success", data: d, error: null }))
      .catch((e) => setHourly({ status: "error", data: null, error: e }));

    getAlertsFor(loc.latitude, loc.longitude, 7)
      .then((d) => setAlerts({ status: "success", data: d, error: null }))
      .catch((e) => setAlerts({ status: "error", data: null, error: e }));
  }, []);

  useEffect(() => {
    if (location) loadAll(location, units);
  }, [location, units, loadAll]);

  // Apply a location + weather snapshot handed back from a chat response,
  // so the dashboard updates from weather_context without a refetch.
  const applyFromChat = useCallback((loc, weatherContext, u) => {
    setLocation(loc);
    if (weatherContext?.current) {
      setCurrent({
        status: "success",
        data: { location: loc, units: u, current: weatherContext.current },
        error: null,
      });
    }
    if (weatherContext?.forecast_daily) {
      setForecast({
        status: "success",
        data: { location: loc, units: u, daily: weatherContext.forecast_daily },
        error: null,
      });
    }
  }, []);

  return {
    location,
    setLocation,
    units,
    setUnits,
    current,
    forecast,
    hourly,
    alerts,
    applyFromChat,
  };
}
