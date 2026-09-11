import { useCallback, useEffect, useRef, useState } from "react";

// Generic idle/loading/success/error runner. Pass a function that returns
// a promise; call `run()` to fire it (or set `immediate` deps to auto-run).
export function useFetch(fn, deps = [], { immediate = true } = {}) {
  const [status, setStatus] = useState("idle"); // idle | loading | success | error
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const requestId = useRef(0);

  const run = useCallback(async (...args) => {
    const id = ++requestId.current;
    setStatus("loading");
    setError(null);
    try {
      const result = await fn(...args);
      if (id === requestId.current) {
        setData(result);
        setStatus("success");
      }
      return result;
    } catch (err) {
      if (id === requestId.current) {
        setError(err);
        setStatus("error");
      }
      throw err;
    }
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (immediate) run();
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps

  return { status, data, error, run, setData };
}
