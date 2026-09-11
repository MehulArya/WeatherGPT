import { useEffect, useRef, useState } from "react";
import { motion, useMotionValue, useSpring } from "framer-motion";

export default function AnimatedNumber({ value, decimals = 0, suffix = "" }) {
  const spring = useSpring(value, { stiffness: 90, damping: 20, mass: 0.6 });
  const [display, setDisplay] = useState(value);
  const first = useRef(true);

  useEffect(() => {
    if (first.current) {
      first.current = false;
      spring.jump(value);
      setDisplay(value);
      return;
    }
    spring.set(value);
  }, [value]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const unsub = spring.on("change", (v) => setDisplay(v));
    return unsub;
  }, [spring]);

  return (
    <span className="tabular">
      {Number.isFinite(display) ? display.toFixed(decimals) : "—"}
      {suffix}
    </span>
  );
}
