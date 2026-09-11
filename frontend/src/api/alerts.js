import { apiFetch, MOCK_MODE } from "./client";
import { mockApi } from "./mock";

export async function getAllAlerts() {
  if (MOCK_MODE) return mockApi.alertsAll();
  return apiFetch(`/api/alerts/`);
}

export async function getAlertsFor(latitude, longitude, days = 7) {
  if (MOCK_MODE) return mockApi.alertsFor(latitude, longitude);
  return apiFetch(`/api/alerts/?latitude=${latitude}&longitude=${longitude}&days=${days}`);
}
