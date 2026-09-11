import { apiFetch, MOCK_MODE } from "./client";
import { mockApi } from "./mock";

export async function listConversations() {
  if (MOCK_MODE) return mockApi.conversationsList();
  return apiFetch(`/api/conversations/`);
}

export async function getConversation(id) {
  if (MOCK_MODE) return mockApi.conversationDetail(id);
  return apiFetch(`/api/conversations/${id}/`);
}
