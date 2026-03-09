import { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";

function App() {
  // ── Theme ──
  const [darkMode, setDarkMode] = useState(() => {
    const stored = localStorage.getItem("theme");
    return stored ? stored === "dark" : true;
  });

  useEffect(() => {
    document.documentElement.setAttribute(
      "data-theme",
      darkMode ? "dark" : "light",
    );
    localStorage.setItem("theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  // ── Sessions ──
  const [sessions, setSessions] = useState(() => {
    const stored = localStorage.getItem("chat_sessions");
    return stored ? JSON.parse(stored) : [];
  });

  const [activeSessionId, setActiveSessionId] = useState(() => {
    const stored = localStorage.getItem("chat_sessions");
    if (!stored) return null;
    const parsed = JSON.parse(stored);
    return parsed.length > 0 ? parsed[0].id : null;
  });

  const [sidebarOpen, setSidebarOpen] = useState(false);

  // ── Persist sessions ──
  const saveSession = (updatedSessions) => {
    setSessions(updatedSessions);
    localStorage.setItem("chat_sessions", JSON.stringify(updatedSessions));
  };

  // ── Create new session ──
  const createNewSession = () => {
    const newSession = {
      id: Date.now().toString(),
      title: "New Chat",
      messages: [
        {
          role: "bot",
          content:
            "Hi! I'm BizBot 👋 Ask me anything about your business — sales, revenue, trends, products and more.",
          route: null,
        },
      ],
      createdAt: new Date().toISOString(),
    };
    const updated = [newSession, ...sessions];
    saveSession(updated);
    setActiveSessionId(newSession.id);
    setSidebarOpen(false);
  };

  // ── Update session messages ──
  const updateSession = (sessionId, messages) => {
    const updated = sessions.map((s) => {
      if (s.id === sessionId) {
        const userMessages = messages.filter((m) => m.role === "user");
        const title = userMessages[0]?.content?.slice(0, 32) || "New Chat";
        return { ...s, messages, title };
      }
      return s;
    });
    saveSession(updated);
  };

  const activeSession = sessions.find((s) => s.id === activeSessionId) || null;

  return (
    <div
      className="flex h-screen w-screen overflow-hidden"
      style={{ background: "var(--bg-primary)" }}
    >
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 md:hidden"
          style={{ background: "rgba(0,0,0,0.6)" }}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={(id) => {
          setActiveSessionId(id);
          setSidebarOpen(false);
        }}
        onNewChat={createNewSession}
        sidebarOpen={sidebarOpen}
        onCloseSidebar={() => setSidebarOpen(false)}
        darkMode={darkMode}
        onToggleTheme={() => setDarkMode((prev) => !prev)}
      />

      <ChatWindow
        session={activeSession}
        onUpdateSession={updateSession}
        onOpenSidebar={() => setSidebarOpen(true)}
        darkMode={darkMode}
      />
    </div>
  );
}

export default App;
