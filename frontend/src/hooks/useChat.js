import { useCallback, useEffect, useState } from "react";
import { sendChat, getChatHealth } from "../api/chat";

export function useChat({ units, onLocationResolved } = {}) {
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | loading | error
  const [health, setHealth] = useState(null);

  useEffect(() => {
    getChatHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: "down", llm_configured: false }));
  }, []);

  const send = useCallback(
    async (text) => {
      if (!text.trim()) return;
      const userMsg = { id: `u-${Date.now()}`, role: "user", content: text };
      setMessages((prev) => [...prev, userMsg]);
      setStatus("loading");
      try {
        const res = await sendChat(text, conversationId, units);
        setConversationId(res.conversation_id);
        const assistantMsg = {
          id: `a-${Date.now()}`,
          role: "assistant",
          content: res.answer,
          needsLocation: res.needs_location,
          language: res.language,
        };
        setMessages((prev) => [...prev, assistantMsg]);
        setStatus("idle");
        if (res.location && !res.needs_location && onLocationResolved) {
          onLocationResolved(res.location, res.weather_context, units);
        }
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          { id: `e-${Date.now()}`, role: "assistant", content: err.message || "Couldn't reach the assistant.", isError: true },
        ]);
        setStatus("error");
      }
    },
    [conversationId, units, onLocationResolved]
  );

  const resumeConversation = useCallback((id, priorMessages) => {
    setConversationId(id);
    setMessages(
      priorMessages.map((m) => ({ id: `h-${m.id}`, role: m.role, content: m.content }))
    );
  }, []);

  return { messages, send, status, health, conversationId, resumeConversation };
}
