import { useState } from "react";

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (!value.trim() || disabled) return;
    onSend(value);
    setValue("");
  }

  return (
    <form className="chat-input-row" onSubmit={handleSubmit}>
      <input
        className="chat-input"
        type="text"
        placeholder="Ask about the sky — “will it rain tomorrow in Jaipur?”"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
        aria-label="Message"
      />
      <button className="chat-send" type="submit" disabled={disabled || !value.trim()}>
        Send
      </button>
    </form>
  );
}
