import { motion } from "framer-motion";

export default function TypingIndicator() {
  return (
    <div className="chat-message chat-message--assistant">
      <div className="chat-bubble chat-bubble--typing">
        <motion.span
          className="typing-bar"
          animate={{ scaleX: [0.2, 1, 0.2] }}
          transition={{ duration: 1.1, repeat: Infinity, ease: [0.65, 0, 0.35, 1] }}
        />
      </div>
    </div>
  );
}
