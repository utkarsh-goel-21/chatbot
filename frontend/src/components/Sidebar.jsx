import {
  PlusCircle,
  MessageSquare,
  X,
  BarChart2,
  Sun,
  Moon,
} from "lucide-react";

function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  sidebarOpen,
  onCloseSidebar,
  darkMode,
  onToggleTheme,
}) {
  const formatTime = (isoString) => {
    const date = new Date(isoString);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  const groupedSessions = sessions.reduce((groups, session) => {
    const label = formatTime(session.createdAt);
    if (!groups[label]) groups[label] = [];
    groups[label].push(session);
    return groups;
  }, {});

  return (
    <div
      className={`
        fixed md:static inset-y-0 left-0 z-30
        w-[270px] h-full flex flex-col
        transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
        md:translate-x-0
      `}
      style={{
        background: "var(--bg-secondary)",
        borderRight: "1px solid var(--border)",
      }}
    >
      {/* ── Logo ── */}
      <div
        className="flex items-center justify-between px-5 pt-5 pb-4"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-xl flex items-center justify-center"
            style={{
              background: "var(--accent)",
              boxShadow: "var(--shadow-accent)",
            }}
          >
            <BarChart2 size={15} className="text-white" />
          </div>
          <span
            className="text-base font-extrabold tracking-tight"
            style={{
              fontFamily: "'Nunito', sans-serif",
              color: "var(--text-primary)",
            }}
          >
            BizBot
          </span>
        </div>

        <button
          onClick={onCloseSidebar}
          className="md:hidden w-7 h-7 rounded-lg flex items-center justify-center"
          style={{ color: "var(--text-muted)" }}
        >
          <X size={15} />
        </button>
      </div>

      {/* ── New Chat Button ── */}
      <div className="px-4 py-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl font-bold text-sm"
          style={{
            fontFamily: "'Nunito', sans-serif",
            background: "var(--accent)",
            color: "#ffffff",
            boxShadow: "var(--shadow-accent)",
          }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.background = "var(--accent-hover)")
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.background = "var(--accent)")
          }
        >
          <PlusCircle size={15} />
          New Chat
        </button>
      </div>

      {/* ── Sessions List ── */}
      <div className="flex-1 overflow-y-auto px-3 py-1">
        {sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 px-4 text-center gap-3">
            <div
              className="w-12 h-12 rounded-2xl flex items-center justify-center"
              style={{ background: "var(--accent-soft)" }}
            >
              <MessageSquare size={18} style={{ color: "var(--accent)" }} />
            </div>
            <p
              className="text-xs leading-relaxed"
              style={{ color: "var(--text-muted)" }}
            >
              No conversations yet.
              <br />
              Hit <strong>New Chat</strong> to begin.
            </p>
          </div>
        ) : (
          Object.entries(groupedSessions).map(([label, groupSessions]) => (
            <div key={label} className="mb-3">
              {/* Group Label */}
              <p
                className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest"
                style={{
                  fontFamily: "'Nunito', sans-serif",
                  color: "var(--text-muted)",
                }}
              >
                {label}
              </p>

              {/* Sessions in group */}
              <div className="space-y-0.5">
                {groupSessions.map((session) => (
                  <button
                    key={session.id}
                    onClick={() => onSelectSession(session.id)}
                    className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-left text-sm transition-all duration-150"
                    style={{
                      background:
                        activeSessionId === session.id
                          ? "var(--accent-soft)"
                          : "transparent",
                      border:
                        activeSessionId === session.id
                          ? "1px solid var(--accent-border)"
                          : "1px solid transparent",
                      color:
                        activeSessionId === session.id
                          ? "var(--accent)"
                          : "var(--text-secondary)",
                    }}
                    onMouseEnter={(e) => {
                      if (activeSessionId !== session.id) {
                        e.currentTarget.style.background = "var(--bg-hover)";
                        e.currentTarget.style.color = "var(--text-primary)";
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (activeSessionId !== session.id) {
                        e.currentTarget.style.background = "transparent";
                        e.currentTarget.style.color = "var(--text-secondary)";
                      }
                    }}
                  >
                    <MessageSquare size={13} className="shrink-0" />
                    <span
                      className="truncate text-xs font-semibold"
                      style={{ fontFamily: "'Nunito', sans-serif" }}
                    >
                      {session.title}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ))
        )}
      </div>

      {/* ── Footer: Theme Toggle ── */}
      <div
        className="px-4 py-4 flex items-center justify-between"
        style={{ borderTop: "1px solid var(--border)" }}
      >
        <div className="flex items-center gap-2">
          <div
            className="w-2 h-2 rounded-full"
            style={{
              background: "#34d399",
              boxShadow: "0 0 6px rgba(52,211,153,0.6)",
            }}
          />
          <span
            className="text-xs font-semibold"
            style={{
              fontFamily: "'Nunito', sans-serif",
              color: "var(--text-muted)",
            }}
          >
            Connected
          </span>
        </div>

        {/* Theme toggle */}
        <button
          onClick={onToggleTheme}
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-bold"
          style={{
            fontFamily: "'Nunito', sans-serif",
            background: "var(--accent-soft)",
            color: "var(--accent)",
            border: "1px solid var(--accent-border)",
          }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.background = "var(--accent)")
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.background = "var(--accent-soft)")
          }
        >
          {darkMode ? (
            <>
              <Sun size={12} /> Light
            </>
          ) : (
            <>
              <Moon size={12} /> Dark
            </>
          )}
        </button>
      </div>
    </div>
  );
}

export default Sidebar;
