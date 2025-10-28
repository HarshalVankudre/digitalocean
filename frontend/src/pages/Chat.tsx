import { useEffect, useState, useMemo } from "react";
import ConversationList from "../components/ConversationList";
import ChatMessage from "../components/ChatMessage";
import { api } from "../lib/api";

/** Types kept lightweight to match existing backend shapes */
type Msg = { id?: string; role: "user" | "assistant"; content: string; isStreaming?: boolean };
type Conv = { id: string; title?: string };

// FIXED: Changed VITE_API_BASE_URL to VITE_API_BASE to match api.ts
const API_BASE = (import.meta.env?.VITE_API_BASE as string | undefined) || "http://localhost:8000";

export default function Chat() {
  const [cid, setCid] = useState<string>("");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [streamingTimer, setStreamingTimer] = useState<NodeJS.Timeout | null>(null);

  // ---------- Init: reopen last, else most recent, else create ----------
  useEffect(() => {
    const init = async () => {
      // 1) try last opened conversation id from localStorage
      const last = localStorage.getItem("cid");
      if (last && (await tryOpen(last))) return;

      // 2) else load list and open the first (most recent)
      try {
        const r = await api.get<Conv[]>("/conversations");
        if (Array.isArray(r.data) && r.data.length > 0) {
          await open(r.data[0].id);
          return;
        }
      } catch {
        /* ignore and create fresh */
      }

      // 3) else create a brand new chat
      await newChat();
    };
    void init();
  }, []);

  const tryOpen = async (id: string) => {
    try {
      await open(id);
      return true;
    } catch {
      return false;
    }
  };

  const newChat = async () => {
    const r = await api.post<Conv>("/conversations", { title: "New chat" });
    const newId = r.data.id;
    localStorage.setItem("cid", newId);
    setCid(newId);
    setMessages([]);
  };

  const open = async (id: string) => {
    const r = await api.get<{ id: string; messages: Msg[] }>(`/conversations/${id}`);
    localStorage.setItem("cid", id);
    setCid(id);
    setMessages(r.data.messages || []);
  };

  // ---------- Streaming helpers ----------
  const appendAssistant = (delta: string) => {
    setMessages((m) => {
      if (m.length && m[m.length - 1].role === "assistant" && m[m.length - 1].isStreaming) {
        const last = m[m.length - 1];
        const updated = { ...last, content: last.content + delta };
        return [...m.slice(0, -1), updated];
      }
      return [...m, { id: "local-a-" + Date.now(), role: "assistant", content: delta, isStreaming: true }];
    });
  };

  // ---------- Send message (streaming; fallback to non-stream) ----------
  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || !cid || busy) return;

    // optimistic user bubble
    const localUserMsg: Msg = { id: "local-u-" + Date.now(), role: "user", content: text };
    setMessages((m) => [...m, localUserMsg]);
    setInput("");
    setBusy(true);

    try {
      // Call streaming endpoint
      const resp = await fetch(`${API_BASE}/conversations/${cid}/messages/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token") || ""}`,
        },
        body: JSON.stringify({ content: text }),
      });

      if (!resp.ok || !resp.body) {
        console.warn("Stream endpoint failed, falling back to non-streaming");
        try {
          const r = await api.post<Msg>(`/conversations/${cid}/messages`, { content: text });
          setMessages((m) => [...m, r.data]);
        } catch (fallbackErr) {
          console.error("Fallback also failed:", fallbackErr);
          setMessages((m) => m.filter((msg) => msg.id !== localUserMsg.id));
        }
        return;
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let done = false;

      while (!done) {
        const { value, done: d } = await reader.read();
        done = d;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (!line.trim()) continue;

            if (line.startsWith("data: ")) {
              const content = line.slice(6);
              if (content === "[DONE]") {
                continue;
              }
              appendAssistant(content);
            }
          }
        }
      }

      // After streaming completes, mark the message as complete so it renders properly
      setMessages((m) => {
        if (m.length && m[m.length - 1].isStreaming) {
          const last = m[m.length - 1];
          return [...m.slice(0, -1), { ...last, isStreaming: false }];
        }
        return m;
      });
    } catch (err) {
      console.error("Error during streaming:", err);
      setMessages((m) => m.filter((msg) => msg.id !== localUserMsg.id));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-56px)]">
      <ConversationList
        selected={cid}
        onSelect={(id) => open(id)}
        onNew={newChat}
      />
      <main className="flex-1">
        <div className="mx-auto flex h-full max-w-3xl flex-col px-4">
          <div className="flex-1 overflow-y-auto py-6">
            {messages.map((m, i) => (
              <ChatMessage
                key={m.id ?? i}
                role={m.role}
                content={m.content}
                isStreaming={m.isStreaming}
              />
            ))}
          </div>

          <form onSubmit={send} className="mb-6 flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything…"
              className="flex-1 rounded-2xl border px-4 py-3 shadow-sm"
            />
            <button
              disabled={busy || !cid}
              className="rounded-2xl bg-slate-900 px-6 py-3 text-white disabled:opacity-60"
            >
              {busy ? "Sending…" : "Send"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}