import { useEffect, useRef } from "react";
import { AnimatePresence } from "framer-motion";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";
import TypingIndicator from "./TypingIndicator";

export default function ChatWindow({ messages, onSend, status, health }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, status]);

  const healthy = health?.llm_configured && health?.status === "ok";

  return (
    <div className="chat-window">
      <div className="chat-window-head">
        <span className="chat-title">Ask WeatherGPT</span>
        <span className="chat-status">
          <span className={`chat-status-dot ${healthy ? "is-healthy" : "is-down"}`} />
          {health ? (healthy ? "Assistant online" : "Assistant unavailable") : "Checking status…"}
        </span>
      </div>

      <div className="chat-scroll" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>Ask a plain question about the weather anywhere.</p>
            <p className="chat-empty-sub">“Will it rain tomorrow in Jaipur?” · “Compare Delhi and Mumbai”</p>
          </div>
        )}
        <AnimatePresence initial={false}>
          {messages.map((m) => (
            <ChatMessage key={m.id} role={m.role} content={m.content} isError={m.isError} />
          ))}
        </AnimatePresence>
        {status === "loading" && <TypingIndicator />}
      </div>

      <ChatInput onSend={onSend} disabled={status === "loading"} />
    </div>
  );
}
