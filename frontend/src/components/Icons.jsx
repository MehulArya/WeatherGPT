// Minimal, geometric, hand-built icons — no icon library, no emoji.
// A shared stroke language (1.5px, currentColor) ties them together.

const base = { fill: "none", stroke: "currentColor", strokeWidth: 1.5, strokeLinecap: "round" };

export function IconSun({ size = 22, ...p }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...p}>
      <circle cx="12" cy="12" r="5" {...base} />
      {[0, 45, 90, 135, 180, 225, 270, 315].map((deg, i) => (
        <line
          key={deg}
          x1="12"
          y1={i % 2 === 0 ? 1 : 2.5}
          x2="12"
          y2={i % 2 === 0 ? 4 : 5}
          transform={`rotate(${deg} 12 12)`}
          {...base}
        />
      ))}
    </svg>
  );
}

export function IconCloud({ size = 22, ...p }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...p}>
      <path d="M6 17a4 4 0 0 1-.7-7.94A5 5 0 0 1 15 7.1 4.5 4.5 0 0 1 17.5 16H6z" {...base} />
    </svg>
  );
}

export function IconRain({ size = 22, ...p }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...p}>
      <path d="M6 13.5a4 4 0 0 1-.7-7.94A5 5 0 0 1 15 3.6 4.5 4.5 0 0 1 17.5 12.5H6z" {...base} />
      <line x1="8" y1="16" x2="7" y2="20" {...base} />
      <line x1="12" y1="16" x2="11" y2="20" {...base} />
      <line x1="16" y1="16" x2="15" y2="20" {...base} />
    </svg>
  );
}

export function IconStorm({ size = 22, ...p }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...p}>
      <path d="M6 12.5a4 4 0 0 1-.7-7.94A5 5 0 0 1 15 2.6 4.5 4.5 0 0 1 17.5 11.5H6z" {...base} />
      <polyline points="12.5 14 10 18.5 13 18.5 10.5 22.5" {...base} />
    </svg>
  );
}

export function IconWind({ size = 22, ...p }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...p}>
      <path d="M3 8h11.5a2.5 2.5 0 1 0-2.4-3.2" {...base} />
      <path d="M3 12.5h15a2.5 2.5 0 1 1-2.4 3.2" {...base} />
      <path d="M3 17h8.5a2 2 0 1 1-1.9 2.6" {...base} />
    </svg>
  );
}

export function IconFog({ size = 22, ...p }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...p}>
      <circle cx="9" cy="9" r="4" opacity="0.5" {...base} />
      <line x1="3" y1="16" x2="21" y2="16" {...base} />
      <line x1="5" y1="19.5" x2="19" y2="19.5" {...base} />
    </svg>
  );
}

export function IconSnow({ size = 22, ...p }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...p}>
      <path d="M6 13a4 4 0 0 1-.7-7.94A5 5 0 0 1 15 3.1 4.5 4.5 0 0 1 17.5 12H6z" {...base} />
      <line x1="8" y1="16" x2="8" y2="21" {...base} />
      <line x1="12" y1="16" x2="12" y2="21" {...base} />
      <line x1="16" y1="16" x2="16" y2="21" {...base} />
    </svg>
  );
}

const CONDITION_MAP = [
  [/clear|sun/i, IconSun],
  [/thunder|storm/i, IconStorm],
  [/heavy rain|rain|drizzle/i, IconRain],
  [/snow/i, IconSnow],
  [/wind/i, IconWind],
  [/haz|fog|mist/i, IconFog],
  [/cloud|overcast/i, IconCloud],
];

export function conditionIcon(condition = "") {
  const match = CONDITION_MAP.find(([re]) => re.test(condition));
  return match ? match[1] : IconCloud;
}

export function IconClose({ size = 16, ...p }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...p}>
      <line x1="5" y1="5" x2="19" y2="19" {...base} />
      <line x1="19" y1="5" x2="5" y2="19" {...base} />
    </svg>
  );
}

export function IconArrowDivider({ size = 20, ...p }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...p}>
      <line x1="12" y1="2" x2="12" y2="22" {...base} strokeDasharray="1.5 4" />
    </svg>
  );
}
