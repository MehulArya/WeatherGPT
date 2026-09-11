import { apiFetch, MOCK_MODE } from "./client";
import { mockApi } from "./mock";

export async function searchLocation(query, count = 5) {
  if (MOCK_MODE) return mockApi.location(query, count);
  return apiFetch(`/api/weather/location/?query=${encodeURIComponent(query)}&count=${count}`);
}

export async function reverseGeocode(latitude, longitude) {
  if (MOCK_MODE) return { name: "Selected location", country: "", latitude, longitude };
  return apiFetch(`/api/weather/location/reverse/?latitude=${latitude}&longitude=${longitude}`);
}

export async function getCurrent(latitude, longitude, units = "metric") {
  if (MOCK_MODE) return mockApi.current(latitude, longitude, units);
  return apiFetch(`/api/weather/current/?latitude=${latitude}&longitude=${longitude}&units=${units}`);
}

export async function getForecast(latitude, longitude, days = 7, units = "metric") {
  if (MOCK_MODE) return mockApi.forecast(latitude, longitude, days, units);
  return apiFetch(`/api/weather/forecast/?latitude=${latitude}&longitude=${longitude}&days=${days}&units=${units}`);
}

export async function getHourly(latitude, longitude, hours = 24, units = "metric") {
  if (MOCK_MODE) return mockApi.hourly(latitude, longitude, hours, units);
  return apiFetch(`/api/weather/hourly/?latitude=${latitude}&longitude=${longitude}&hours=${hours}&units=${units}`);
}

export async function compareCities(city1, city2, units = "metric") {
  if (MOCK_MODE) return mockApi.compare(city1, city2, units);
  return apiFetch(`/api/weather/compare/?city1=${encodeURIComponent(city1)}&city2=${encodeURIComponent(city2)}&units=${units}`);
}
