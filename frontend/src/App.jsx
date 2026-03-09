import { useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";

function App() {
  const [sessions, setSessions] = useState(() => {
    const stored = localStorage.getItem("chat_sessions");
    return stored ? JSON.parse(stored) : [];
  });
  const [activeSessionId, setActiveSessionId] = useState(null);

  const saveSession = (updatedSessions) => {
    setSessions(updatedSessions);
    localStorage.setItem("chat_sessions", JSON.stringify(updatedSessions));
  };

  const createNewSession = () => {
    const newSession = {
      id: Date.now().toString(),
      title: "New Chat",
      messages: [],
      createdAt: new Date().toISOString(),
    };
    const updated = [newSession, ...sessions];
    saveSession(updated);
    setActiveSessionId(newSession.id);
  };

  const updateSession = (sessionId, messages) => {
    const updated = sessions.map((s) => {
      if (s.id === sessionId) {
        const title = messages[0]?.content?.slice(0, 30) || "New Chat";
        return { ...s, messages, title };
      }
      return s;
    });
    saveSession(updated);
  };

  const activeSession = sessions.find((s) => s.id === activeSessionId) || null;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0a0a0a]">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        onNewChat={createNewSession}
      />
      <ChatWindow session={activeSession} onUpdateSession={updateSession} />
    </div>
  );
}

export default App;
