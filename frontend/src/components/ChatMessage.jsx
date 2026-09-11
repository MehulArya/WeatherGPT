import { motion } from "framer-motion";

export default function ChatMessage({ role, content, isError }) {
  const lines = content.split(/(?<=[.?!])\s+/).filter(Boolean);

  return (
    <div className={`chat-message chat-message--${role}`}>
      <div className={`chat-bubble ${isError ? "chat-bubble--error" : ""}`}>
        {lines.map((line, i) => (
          <motion.span
            key={i}
            className="chat-line"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: i * 0.08, ease: [0.16, 1, 0.3, 1] }}
          >
            {line}{" "}
          </motion.span>
        ))}
      </div>
    </div>
  );
}
