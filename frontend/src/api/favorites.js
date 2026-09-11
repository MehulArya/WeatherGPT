import { apiFetch, MOCK_MODE } from "./client";
import { mockApi } from "./mock";

export async function listFavorites(clientKey) {
  if (MOCK_MODE) return mockApi.favoritesList(clientKey);
  return apiFetch(`/api/favorites/?client_key=${encodeURIComponent(clientKey)}`);
}

export async function addFavorite(payload) {
  if (MOCK_MODE) return mockApi.favoriteAdd(payload);
  return apiFetch(`/api/favorites/`, { method: "POST", body: JSON.stringify(payload) });
}

export async function removeFavorite(id, clientKey) {
  if (MOCK_MODE) return mockApi.favoriteRemove(id, clientKey);
  return apiFetch(`/api/favorites/${id}/?client_key=${encodeURIComponent(clientKey)}`, { method: "DELETE" });
}

export function getClientKey() {
  let key = localStorage.getItem("weathergpt_client_key");
  if (!key) {
    key = crypto.randomUUID();
    localStorage.setItem("weathergpt_client_key", key);
  }
  return key;
}
