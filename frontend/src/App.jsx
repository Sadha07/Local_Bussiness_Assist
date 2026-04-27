import React, { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const LOADING_STEPS = [
  "Searching data sources...",
  "Looking through business details...",
  "Reading reviews and signals...",
  "Summarizing key insights...",
];

const makeId = () => {
  if (window.crypto && window.crypto.randomUUID) {
    return `local-business-${window.crypto.randomUUID()}`;
  }
  return `local-business-${Date.now()}`;
};

const getApiBase = () => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl) {
    return envUrl.replace(/\/$/, "");
  }
  return "http://localhost:8000";
};

function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Vanakkam! I am Chennai Scout. Ask me for PGs, food, or shops in your area and I will pull live review insights.",
    },
  ]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState("connecting");
  const [isLoading, setIsLoading] = useState(false);
  const [loadingIndex, setLoadingIndex] = useState(0);
  const [sessionId, setSessionId] = useState(makeId());
  const scrollerRef = useRef(null);
  const abortRef = useRef(null);

  const apiBase = getApiBase();

  useEffect(() => {
    const runHealthCheck = async () => {
      try {
        const response = await fetch(`${apiBase}/health`);
        setStatus(response.ok ? "online" : "offline");
      } catch {
        setStatus("offline");
      }
    };

    runHealthCheck();

    return () => {
      if (abortRef.current) {
        abortRef.current.abort();
      }
    };
  }, [apiBase]);

  useEffect(() => {
    if (!isLoading) {
      return;
    }

    const timer = window.setInterval(() => {
      setLoadingIndex((prev) => (prev + 1) % LOADING_STEPS.length);
    }, 1700);

    return () => {
      window.clearInterval(timer);
    };
  }, [isLoading]);

  useEffect(() => {
    if (scrollerRef.current) {
      scrollerRef.current.scrollTop = scrollerRef.current.scrollHeight;
    }
  }, [messages, status]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || isLoading) {
      return;
    }

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setIsLoading(true);
    setLoadingIndex(0);

    if (abortRef.current) {
      abortRef.current.abort();
    }
    abortRef.current = new AbortController();

    try {
      const response = await fetch(`${apiBase}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          content: text,
          session_id: sessionId,
        }),
        signal: abortRef.current.signal,
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Request failed");
      }

      setMessages((prev) => [...prev, { role: "assistant", content: payload.content || "" }]);
      if (payload.session_id) {
        setSessionId(payload.session_id);
      }
      setStatus("online");
    } catch (err) {
      if (err.name === "AbortError") {
        return;
      }
      setStatus("offline");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${err.message || "Unable to reach server."}`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const onComposerSubmit = (event) => {
    event.preventDefault();
    sendMessage();
  };

  const onInputKeyDown = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      sendMessage();
    }
  };

  const resetConversation = () => {
    if (abortRef.current) {
      abortRef.current.abort();
    }
    setMessages([
      {
        role: "assistant",
        content:
          "Fresh chat started. Tell me your area and whether you need PG, food, or shops.",
      },
    ]);
    setIsLoading(false);
    setStatus("online");
    setSessionId(makeId());
  };

  const isOnline = status === "online";

  return (
    <div className="page-shell">
      <div className="orb orb-a" />
      <div className="orb orb-b" />

      <main className="chat-card">
        <header className="chat-header">
          <h1>Local Bussiness Agent</h1>
          <div className={`status-pill ${isOnline ? "status-online" : "status-offline"}`}>
            <span className="dot" />
            {isOnline ? "ONLINE" : "OFFLINE"}
          </div>
        </header>

        <section className="chat-feed" ref={scrollerRef}>
          {messages.map((msg, idx) => (
            <article className={`bubble ${msg.role}`} key={`${msg.role}-${idx}`}>
              <span className="role-label">{msg.role === "user" ? "You" : "Scout"}</span>
              <div className="message-markdown">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
              </div>
            </article>
          ))}
          {isLoading ? (
            <article className="loader-card" aria-live="polite">
              <div className="loader-dots">
                <span />
                <span />
                <span />
              </div>
              <p>{LOADING_STEPS[loadingIndex]}</p>
            </article>
          ) : null}
        </section>

        <form className="composer" onSubmit={onComposerSubmit}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onInputKeyDown}
            placeholder="Try: best women PG in Velachery"
          />
          <button type="submit" disabled={isLoading || !input.trim()}>
            {isLoading ? "Sending..." : "Send"}
          </button>
          <button type="button" className="secondary" onClick={resetConversation}>
            New Chat
          </button>
        </form>
      </main>
    </div>
  );
}

export default App;
