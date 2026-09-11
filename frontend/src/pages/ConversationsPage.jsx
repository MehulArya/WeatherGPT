import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { listConversations, getConversation } from "../api/conversations";
import ChatMessage from "../components/ChatMessage";
import ChatInput from "../components/ChatInput";
import { useChat } from "../hooks/useChat";
import { useWeather } from "../hooks/useWeather";

const REL_FMT = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });

function relativeTime(iso) {
  const diffMs = new Date(iso) - new Date();
  const diffH = Math.round(diffMs / 3600000);
  if (Math.abs(diffH) < 24) return REL_FMT.format(diffH, "hour");
  return REL_FMT.format(Math.round(diffH / 24), "day");
}

export default function ConversationsPage({ units }) {
  const [status, setStatus] = useState("loading");
  const [list, setList] = useState([]);
  const [error, setError] = useState(null);
  const [activeId, setActiveId] = useState(null);

  const weather = useWeather(units);
  const chat = useChat({ units: weather.units, onLocationResolved: weather.applyFromChat });

  useEffect(() => {
    listConversations()
      .then((data) => {
        setList(data);
        setStatus("success");
      })
      .catch((err) => {
        setError(err);
        setStatus("error");
      });
  }, []);

  async function openThread(id) {
    setActiveId(id);
    const detail = await getConversation(id);
    chat.resumeConversation(id, detail.messages);
  }

  return (
    <div className="container conversations-page">
      <h1 className="page-heading">Conversations</h1>

      {status === "loading" && <div className="skeleton" style={{ height: 200 }} />}
      {status === "error" && <p className="section-error">{error?.message}</p>}
      {status === "success" && list.length === 0 && (
        <p className="chat-empty-sub">No conversations yet. Ask the assistant something from the dashboard.</p>
      )}

      <ul className="conversation-list">
        {list.map((c) => (
          <li key={c.id}>
            <button
              className={`conversation-row ${activeId === c.id ? "is-active" : ""}`}
              onClick={() => openThread(c.id)}
            >
              <span className="conversation-title">{c.title}</span>
              <span className="conversation-time tabular">{relativeTime(c.updated_at)}</span>
            </button>
          </li>
        ))}
      </ul>

      <AnimatePresence>
        {activeId && (
          <motion.div
            className="conversation-thread"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.45, ease: [0.65, 0, 0.35, 1] }}
          >
            <div className="chat-scroll chat-scroll--embedded">
              {chat.messages.map((m) => (
                <ChatMessage key={m.id} role={m.role} content={m.content} />
              ))}
            </div>
            <ChatInput onSend={chat.send} disabled={chat.status === "loading"} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
