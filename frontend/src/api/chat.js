import { apiFetch, MOCK_MODE } from "./client";
import { mockApi } from "./mock";

export async function sendChat(message, conversationId, units = "metric") {
  if (MOCK_MODE) return mockApi.chat(message, conversationId, units);
  return apiFetch(`/api/chat/`, {
    method: "POST",
    body: JSON.stringify({ message, conversation_id: conversationId, units }),
  });
}

export async function getChatHealth() {
  if (MOCK_MODE) return mockApi.chatHealth();
  return apiFetch(`/api/chat/health/`);
}
