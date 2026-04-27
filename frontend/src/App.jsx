import React, { useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

const assistantWelcome = {
  role: "assistant",
  content:
    "Hi, I am your local business assistant. Share category, area, and budget, and I will guide you with options and review insights.",
};

const isDashSeparatorLine = (line) => {
  const stripped = line.trim();
  return stripped.length >= 3 && /^[-\s]+$/.test(stripped);
};

const splitCells = (line) => line.split("|").map((cell) => cell.trim()).filter(Boolean);

const isAsciiBorderLine = (line) => {
  const stripped = line.trim();
  return stripped.length >= 3 && /^\+[\-+]+\+$/.test(stripped);
};

const isAsciiRowLine = (line) => {
  const stripped = line.trim();
  return stripped.startsWith("|") && stripped.endsWith("|") && stripped.includes("|");
};

const splitAsciiCells = (line) =>
  line
    .trim()
    .slice(1, -1)
    .split("|")
    .map((cell) => cell.trim());

// Accepts "table-like" plain text and converts it into valid markdown tables.
const normalizeTableLikeMarkdown = (content) => {
  const lines = content.split("\n");
  const output = [];

  let i = 0;
  while (i < lines.length) {
    // ASCII box table support, e.g. +----+..+ with | cell | rows.
    if (isAsciiBorderLine(lines[i])) {
      let j = i + 1;
      const rowLines = [];

      while (j < lines.length) {
        if (isAsciiRowLine(lines[j])) {
          rowLines.push(lines[j]);
          j += 1;
          continue;
        }
        if (isAsciiBorderLine(lines[j])) {
          j += 1;
          continue;
        }
        break;
      }

      if (rowLines.length >= 2) {
        const headerCells = splitAsciiCells(rowLines[0]);
        const colCount = headerCells.length;
        output.push(`| ${headerCells.join(" | ")} |`);
        output.push(`| ${Array(colCount).fill("---").join(" | ")} |`);

        for (const row of rowLines.slice(1)) {
          const cells = splitAsciiCells(row);
          const normalized = cells.slice(0, colCount);
          while (normalized.length < colCount) {
            normalized.push("");
          }
          output.push(`| ${normalized.join(" | ")} |`);
        }

        i = j;
        continue;
      }
    }

    const current = lines[i];
    const next = i + 1 < lines.length ? lines[i + 1] : "";

    const looksLikeHeader = (current.match(/\|/g) || []).length >= 2;
    const looksLikeSeparator = isDashSeparatorLine(next);

    if (looksLikeHeader && looksLikeSeparator) {
      const headerCells = splitCells(current);
      if (headerCells.length >= 2) {
        const colCount = headerCells.length;
        output.push(`| ${headerCells.join(" | ")} |`);
        output.push(`| ${Array(colCount).fill("---").join(" | ")} |`);

        i += 2;
        while (i < lines.length) {
          const row = lines[i];
          const rowLooksLikeData = (row.match(/\|/g) || []).length >= 2;
          if (!rowLooksLikeData) {
            break;
          }

          const cells = splitCells(row);
          const normalized = cells.slice(0, colCount);
          while (normalized.length < colCount) {
            normalized.push("");
          }
          output.push(`| ${normalized.join(" | ")} |`);
          i += 1;
        }
        continue;
      }
    }

    output.push(current);
    i += 1;
  }

  return output.join("\n");
};

function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "light");
  const [messages, setMessages] = useState([assistantWelcome]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sessionId, setSessionId] = useState(() => {
    if (window.crypto && window.crypto.randomUUID) {
      return `local-business-${window.crypto.randomUUID()}`;
    }
    return `local-business-${Date.now()}`;
  });
  const messagesEndRef = useRef(null);
  const abortRef = useRef(null);

  const canSend = useMemo(() => input.trim().length > 0 && !loading, [input, loading]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);

    return () => {
      if (abortRef.current) {
        abortRef.current.abort();
      }
    };
  }, [theme]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) {
      return;
    }

    setError("");
    const nextMessages = [...messages, { role: "user", content: text }];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);

    if (abortRef.current) {
      abortRef.current.abort();
    }
    abortRef.current = new AbortController();

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
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

      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload?.detail || `HTTP ${response.status}`);
      }

      const answer = payload?.content || "No response from assistant.";
      setMessages((prev) => [...prev, { role: "assistant", content: answer }]);
      if (payload.session_id) {
        setSessionId(payload.session_id);
      }
    } catch (err) {
      if (err.name === "AbortError") {
        return;
      }
      setError(err.message || "Unable to connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  const onComposerSubmit = (event) => {
    event.preventDefault();
    sendMessage();
  };

  const onInputKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const resetConversation = () => {
    if (loading) {
      return;
    }
    if (abortRef.current) {
      abortRef.current.abort();
    }
    setMessages([assistantWelcome]);
    setInput("");
    setError("");
    if (window.crypto && window.crypto.randomUUID) {
      setSessionId(`local-business-${window.crypto.randomUUID()}`);
    } else {
      setSessionId(`local-business-${Date.now()}`);
    }
  };

  const toggleTheme = () => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  };

  return (
    <div className="page">
      <main className="app-card">
        <header className="card-header">
          <div>
            <h1>Local Business Assistant</h1>
            <p>Ask about PGs, food places, shops, and review insights by area and budget.</p>
          </div>
          <div className="header-actions">
            <button type="button" className="theme-btn" onClick={toggleTheme}>
              {theme === "light" ? "Dark Mode" : "Light Mode"}
            </button>
            <span className="status-pill">Online</span>
          </div>
        </header>

        <section className="messages" aria-live="polite">
          {messages.map((msg, idx) => (
            <article className={`bubble ${msg.role}`} key={`${msg.role}-${idx}`}>
              <p className="role-label">{msg.role === "assistant" ? "Assistant" : "You"}</p>
              {msg.role === "assistant" ? (
                <div className="markdown-body">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {normalizeTableLikeMarkdown(msg.content)}
                  </ReactMarkdown>
                </div>
              ) : (
                <p className="user-text">{msg.content}</p>
              )}
            </article>
          ))}
          {loading ? <article className="bubble assistant pending">Thinking...</article> : null}
          <div ref={messagesEndRef} />
        </section>

        <form className="composer" onSubmit={onComposerSubmit}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onInputKeyDown}
            placeholder="Try: best women PG in Velachery under 10k"
            rows={2}
          />
          <div className="composer-actions">
            <button type="submit" disabled={!canSend}>
              Send
            </button>
            <button
              type="button"
              className="secondary-btn"
              onClick={resetConversation}
              disabled={loading}
            >
              New Chat
            </button>
          </div>
        </form>

        {error ? <p className="error">{error}</p> : null}
      </main>
    </div>
  );
}

export default App;
