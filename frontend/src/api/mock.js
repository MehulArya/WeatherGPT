// Simulated backend so the frontend is fully demoable without Django running.
// Every shape here matches the documented API contract exactly — swapping
// MOCK_MODE off in client.js and pointing the proxy at a real server requires
// no changes to hooks or components.

const CITY_DB = [
  { name: "Jaipur", country: "India", latitude: 26.91962, longitude: 75.78781 },
  { name: "Delhi", country: "India", latitude: 28.6139, longitude: 77.209 },
  { name: "Mumbai", country: "India", latitude: 19.076, longitude: 72.8777 },
  { name: "Udaipur", country: "India", latitude: 24.5854, longitude: 73.7125 },
  { name: "Jodhpur", country: "India", latitude: 26.2389, longitude: 73.0243 },
  { name: "Bengaluru", country: "India", latitude: 12.9716, longitude: 77.5946 },
  { name: "Kolkata", country: "India", latitude: 22.5726, longitude: 88.3639 },
  { name: "London", country: "United Kingdom", latitude: 51.5072, longitude: -0.1276 },
  { name: "New York", country: "United States", latitude: 40.7128, longitude: -74.006 },
  { name: "Tokyo", country: "Japan", latitude: 35.6762, longitude: 139.6503 },
];

const CONDITIONS = [
  "Clear sky",
  "Partly cloudy",
  "Overcast",
  "Light rain",
  "Heavy rain",
  "Thunderstorm",
  "Windy",
  "Hazy",
];

function delay(ms = 550) {
  return new Promise((r) => setTimeout(r, ms + Math.random() * 250));
}

function seededRandom(seed) {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function conditionFor(seed) {
  return CONDITIONS[Math.floor(seededRandom(seed) * CONDITIONS.length)];
}

function toImperial(c) {
  return Math.round((c * 9) / 5 + 32);
}

function kmhToMph(k) {
  return Math.round(k * 0.621371);
}

function mmToIn(mm) {
  return Math.round(mm * 0.0393701 * 100) / 100;
}

function currentFor(loc, units) {
  const seed = loc.latitude + loc.longitude + new Date().getHours();
  const baseTemp = 18 + seededRandom(seed) * 18; // 18–36 C
  const tempC = Math.round(baseTemp * 10) / 10;
  const feelsC = Math.round((baseTemp + seededRandom(seed + 1) * 4 - 1) * 10) / 10;
  const humidity = Math.round(30 + seededRandom(seed + 2) * 65);
  const windKmh = Math.round(seededRandom(seed + 3) * 28 * 10) / 10;
  const precipMm = Math.round(seededRandom(seed + 4) * 8 * 10) / 10;
  const condition = conditionFor(seed + 5);

  if (units === "imperial") {
    return {
      location: { name: loc.name, latitude: loc.latitude, longitude: loc.longitude },
      units: "imperial",
      current: {
        temperature_f: toImperial(tempC),
        feels_like_f: toImperial(feelsC),
        humidity_pct: humidity,
        wind_mph: kmhToMph(windKmh),
        precipitation_in: mmToIn(precipMm),
        condition,
      },
    };
  }

  return {
    location: { name: loc.name, latitude: loc.latitude, longitude: loc.longitude },
    units: "metric",
    current: {
      temperature_c: tempC,
      feels_like_c: feelsC,
      humidity_pct: humidity,
      wind_kmh: windKmh,
      precipitation_mm: precipMm,
      condition,
    },
  };
}

function forecastFor(loc, days, units) {
  const daily = Array.from({ length: days }, (_, i) => {
    const seed = loc.latitude + loc.longitude + i * 3.3;
    const maxC = 24 + seededRandom(seed) * 14;
    const minC = maxC - 6 - seededRandom(seed + 1) * 6;
    const precipProb = Math.round(seededRandom(seed + 2) * 100);
    const precipMm = Math.round(seededRandom(seed + 3) * 12 * 10) / 10;
    const windMaxKmh = Math.round(seededRandom(seed + 4) * 32 * 10) / 10;
    const date = new Date();
    date.setDate(date.getDate() + i);
    const iso = date.toISOString().slice(0, 10);

    if (units === "imperial") {
      return {
        date: iso,
        temperature_max_f: toImperial(maxC),
        temperature_min_f: toImperial(minC),
        precipitation_probability_pct: precipProb,
        precipitation_in: mmToIn(precipMm),
        wind_max_mph: kmhToMph(windMaxKmh),
        condition: conditionFor(seed + 5),
      };
    }
    return {
      date: iso,
      temperature_max_c: Math.round(maxC * 10) / 10,
      temperature_min_c: Math.round(minC * 10) / 10,
      precipitation_probability_pct: precipProb,
      precipitation_mm: precipMm,
      wind_max_kmh: windMaxKmh,
      condition: conditionFor(seed + 5),
    };
  });

  return {
    location: { name: loc.name, latitude: loc.latitude, longitude: loc.longitude },
    units,
    daily,
  };
}

function hourlyFor(loc, hours, units) {
  const now = new Date();
  const hourly = Array.from({ length: hours }, (_, i) => {
    const seed = loc.latitude + loc.longitude + i * 1.7;
    const tempC = 20 + seededRandom(seed) * 14;
    const precipProb = Math.round(seededRandom(seed + 1) * 100);
    const precipMm = Math.round(seededRandom(seed + 2) * 5 * 10) / 10;
    const windKmh = Math.round(seededRandom(seed + 3) * 22 * 10) / 10;
    const t = new Date(now.getTime() + i * 3600 * 1000);
    const iso = t.toISOString().slice(0, 13) + ":00";

    if (units === "imperial") {
      return {
        time: iso,
        temperature_f: toImperial(tempC),
        precipitation_probability_pct: precipProb,
        precipitation_in: mmToIn(precipMm),
        wind_mph: kmhToMph(windKmh),
        condition: conditionFor(seed + 4),
      };
    }
    return {
      time: iso,
      temperature_c: Math.round(tempC * 10) / 10,
      precipitation_probability_pct: precipProb,
      precipitation_mm: precipMm,
      wind_kmh: windKmh,
      condition: conditionFor(seed + 4),
    };
  });

  return {
    location: { name: loc.name, latitude: loc.latitude, longitude: loc.longitude },
    units,
    hourly,
  };
}

function findCity(query) {
  if (!query) return [];
  const q = query.toLowerCase();
  return CITY_DB.filter((c) => c.name.toLowerCase().includes(q));
}

function findExact(name) {
  return CITY_DB.find((c) => c.name.toLowerCase() === String(name).toLowerCase());
}

// ---- in-memory "database" for favorites / conversations ----
let favorites = [];
let favoriteId = 1;
let conversations = [];
let conversationId = 1;
let messageId = 1;
let alertsStore = [];
let alertId = 1;

function makeAlerts(loc) {
  const seed = loc.latitude + loc.longitude;
  const types = [];
  if (seededRandom(seed) > 0.4)
    types.push({
      alert_type: "rain",
      severity: seededRandom(seed + 1) > 0.6 ? "high" : "medium",
      title: `Heavy rain likely near ${loc.name}`,
      description: `Rainfall accumulation is trending upward over the next 24–48 hours around ${loc.name}.`,
      advice: "Carry rain protection and allow extra travel time.",
    });
  if (seededRandom(seed + 2) > 0.55)
    types.push({
      alert_type: "heat",
      severity: seededRandom(seed + 3) > 0.7 ? "high" : "low",
      title: `Elevated daytime heat in ${loc.name}`,
      description: `Afternoon temperatures are running above the seasonal average for ${loc.name}.`,
      advice: "Stay hydrated and limit exposure between 12–4pm.",
    });
  if (seededRandom(seed + 4) > 0.7)
    types.push({
      alert_type: "wind",
      severity: "medium",
      title: `Gusty conditions expected in ${loc.name}`,
      description: `Wind speeds may exceed comfortable outdoor thresholds around ${loc.name}.`,
      advice: "Secure loose outdoor items.",
    });

  return types.map((t) => ({
    id: alertId++,
    location_name: loc.name,
    latitude: String(loc.latitude),
    longitude: String(loc.longitude),
    starts_at: new Date().toISOString(),
    ends_at: new Date(Date.now() + 48 * 3600 * 1000).toISOString(),
    source: "prototype-rule-engine",
    is_official: false,
    created_at: new Date().toISOString(),
    ...t,
  }));
}

// ---- chat "LLM" mock ----
function craftAnswer(message, loc, units) {
  const lower = message.toLowerCase();
  const current = loc ? currentFor(loc, units) : null;
  const forecast = loc ? forecastFor(loc, 3, units) : null;

  const isHindi = /baarish|barish|mausam|kya|kal|aaj|namaste/.test(lower);

  if (!loc) {
    return {
      answer: isHindi
        ? "Kis shehar ke baare mein jaanna chahte hain?"
        : "Which city do you mean? Tell me a place and I'll check.",
      language: isHindi ? "hi" : "en",
      needs_location: true,
      intent: "advisory",
      location: null,
      weather_context: null,
    };
  }

  const tempKey = units === "imperial" ? "temperature_f" : "temperature_c";
  const unitLabel = units === "imperial" ? "°F" : "°C";
  const tomorrow = forecast.daily[1];
  const rainProb = tomorrow.precipitation_probability_pct;

  let answer;
  let intent = "current_weather";

  if (lower.includes("rain") || lower.includes("baarish")) {
    intent = "forecast";
    answer = isHindi
      ? `${loc.name} mein kal baarish ka chance ${rainProb}% hai. ${
          rainProb > 50 ? "Chhata saath rakhein." : "Zyada chance nahi hai, lekin nazar rakhein."
        }`
      : `In ${loc.name}, tomorrow's rain chance sits at ${rainProb}%. ${
          rainProb > 50
            ? "Worth carrying something waterproof."
            : "Not high, but the forecast can shift a little closer to the day."
        }`;
  } else if (lower.includes("day after") || lower.includes("compare")) {
    intent = "forecast";
    const dayAfter = forecast.daily[2];
    answer = `The day after, ${loc.name} is looking at a high near ${
      dayAfter[units === "imperial" ? "temperature_max_f" : "temperature_max_c"]
    }${unitLabel} with ${dayAfter.precipitation_probability_pct}% rain chance — ${dayAfter.condition.toLowerCase()}.`;
  } else {
    answer = `Right now in ${loc.name}, it's ${current.current[tempKey]}${unitLabel} and ${current.current.condition.toLowerCase()}, feeling closer to ${
      current.current[units === "imperial" ? "feels_like_f" : "feels_like_c"]
    }${unitLabel}.`;
  }

  return {
    answer,
    language: isHindi ? "hi" : "en",
    needs_location: false,
    intent,
    location: { name: loc.name, latitude: loc.latitude, longitude: loc.longitude },
    weather_context: {
      current: current.current,
      forecast_daily: forecast.daily,
      units,
    },
  };
}

export const mockApi = {
  async location(query, count = 5) {
    await delay(300);
    return { results: findCity(query).slice(0, count) };
  },

  async current(latitude, longitude, units = "metric") {
    await delay();
    const loc =
      CITY_DB.find(
        (c) => Math.abs(c.latitude - latitude) < 0.01 && Math.abs(c.longitude - longitude) < 0.01
      ) || { name: "Selected location", latitude, longitude };
    return currentFor(loc, units);
  },

  async forecast(latitude, longitude, days = 7, units = "metric") {
    await delay();
    const loc =
      CITY_DB.find(
        (c) => Math.abs(c.latitude - latitude) < 0.01 && Math.abs(c.longitude - longitude) < 0.01
      ) || { name: "Selected location", latitude, longitude };
    return forecastFor(loc, days, units);
  },

  async hourly(latitude, longitude, hours = 24, units = "metric") {
    await delay();
    const loc =
      CITY_DB.find(
        (c) => Math.abs(c.latitude - latitude) < 0.01 && Math.abs(c.longitude - longitude) < 0.01
      ) || { name: "Selected location", latitude, longitude };
    return hourlyFor(loc, hours, units);
  },

  async compare(city1, city2, units = "metric") {
    await delay(700);
    const a = findExact(city1);
    const b = findExact(city2);
    if (!a || !b) {
      throw { error: { code: "LOCATION_NOT_FOUND", message: "One of those cities wasn't found." } };
    }
    return {
      units,
      comparison: [
        { location: { name: a.name, latitude: a.latitude, longitude: a.longitude }, units, current: currentFor(a, units).current },
        { location: { name: b.name, latitude: b.latitude, longitude: b.longitude }, units, current: currentFor(b, units).current },
      ],
    };
  },

  async alertsAll() {
    await delay(300);
    return alertsStore;
  },

  async alertsFor(latitude, longitude) {
    await delay(400);
    const loc =
      CITY_DB.find(
        (c) => Math.abs(c.latitude - latitude) < 0.01 && Math.abs(c.longitude - longitude) < 0.01
      ) || { name: "Selected location", latitude, longitude };
    const fresh = makeAlerts(loc);
    alertsStore = [...alertsStore.filter((a) => a.location_name !== loc.name), ...fresh];
    return fresh;
  },

  async chatHealth() {
    await delay(150);
    return { status: "ok", llm_configured: true, llm_model: "weathergpt-mock-1" };
  },

  async chat(message, conversationIdParam, units = "metric") {
    await delay(900);
    let convo = conversations.find((c) => c.id === conversationIdParam);
    if (!convo) {
      convo = { id: conversationId++, title: message.slice(0, 40), created_at: new Date().toISOString(), updated_at: new Date().toISOString(), messages: [] };
      conversations.push(convo);
    }

    // resolve a location: explicit mention in the message wins, else reuse the conversation's last one
    let loc = CITY_DB.find((c) => message.toLowerCase().includes(c.name.toLowerCase()));
    if (!loc) loc = convo.lastLocation;
    if (loc) convo.lastLocation = loc;

    const result = craftAnswer(message, loc, units);

    convo.messages.push({ id: messageId++, role: "user", content: message, metadata: {}, created_at: new Date().toISOString() });
    convo.messages.push({ id: messageId++, role: "assistant", content: result.answer, metadata: { intent: result.intent }, created_at: new Date().toISOString() });
    convo.updated_at = new Date().toISOString();

    return { ...result, conversation_id: convo.id };
  },

  async conversationsList() {
    await delay(300);
    return conversations
      .map((c) => ({ id: c.id, title: c.title, created_at: c.created_at, updated_at: c.updated_at }))
      .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
  },

  async conversationDetail(id) {
    await delay(300);
    const convo = conversations.find((c) => c.id === Number(id));
    if (!convo) throw { error: { code: "LOCATION_NOT_FOUND", message: "Conversation not found." } };
    return { id: convo.id, title: convo.title, created_at: convo.created_at, updated_at: convo.updated_at, messages: convo.messages };
  },

  async favoritesList(clientKey) {
    await delay(300);
    return favorites.filter((f) => f.client_key === clientKey);
  },

  async favoriteAdd(payload) {
    await delay(400);
    const row = { id: favoriteId++, created_at: new Date().toISOString(), ...payload };
    favorites.push(row);
    return row;
  },

  async favoriteRemove(id, clientKey) {
    await delay(300);
    const before = favorites.length;
    favorites = favorites.filter((f) => !(f.id === Number(id) && f.client_key === clientKey));
    if (favorites.length === before) {
      throw { error: { code: "LOCATION_NOT_FOUND", message: "Favorite not found." } };
    }
    return true;
  },
};
