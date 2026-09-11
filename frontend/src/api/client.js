// Every real call in this app is a relative URL like "/api/weather/current/"
// — no base URL, no CORS handling — proxied to Django in dev (vite.config.js).
//
// MOCK_MODE lets the frontend run and demo fully without the Django backend
// running. Flip to false (or set VITE_USE_MOCKS=false) once the backend is
// reachable at /api — every resource module below calls the same shape of
// endpoint either way, so nothing else has to change.
export const MOCK_MODE = import.meta.env.VITE_MOCK === "true";

export class ApiError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
  }
}

const FRIENDLY_MESSAGES = {
  LOCATION_NOT_FOUND: "Couldn't find that place. Try a different spelling.",
  INVALID_QUERY: "That search didn't make sense to the weather service.",
  WEATHER_PROVIDER_ERROR: "The weather service is unavailable right now.",
  LLM_ERROR: "The assistant couldn't respond. Try asking again.",
  RATE_LIMITED: "Too many requests — wait a moment and try again.",
};

export function friendlyError(code, fallback) {
  return FRIENDLY_MESSAGES[code] || fallback || "Something went wrong.";
}

export async function apiFetch(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  let body = null;
  try {
    body = await res.json();
  } catch {
    // no JSON body
  }

  if (!res.ok || (body && body.error)) {
    const code = body?.error?.code || "WEATHER_PROVIDER_ERROR";
    const message = friendlyError(code, body?.error?.message);
    throw new ApiError(code, message);
  }

  return body;
}
