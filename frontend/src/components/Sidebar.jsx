import { PlusCircle, MessageSquare, X } from "lucide-react";

function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  sidebarOpen,
  onCloseSidebar,
}) {
  return (
    <>
      {/* Sidebar */}
      <div
        className={`
        fixed md:static inset-y-0 left-0 z-30
        w-[260px] h-full flex flex-col
        bg-[#111111] border-r border-white/5
        transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
        md:translate-x-0
      `}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-white/5">
          <span className="text-white font-semibold text-sm tracking-widest uppercase">
            Bizbot
          </span>
          {/* Close button — mobile only */}
          <button
            onClick={onCloseSidebar}
            className="md:hidden text-white/40 hover:text-white transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="px-3 py-3">
          <button
            onClick={onNewChat}
            className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg
              text-white/70 hover:text-white hover:bg-white/5
              border border-white/10 hover:border-white/20
              transition-all duration-200 text-sm"
          >
            <PlusCircle size={16} />
            New Chat
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
          {sessions.length === 0 && (
            <p className="text-white/20 text-xs text-center mt-8 px-4">
              No conversations yet.
              <br />
              Start a new chat.
            </p>
          )}
          {sessions.map((session) => (
            <button
              key={session.id}
              onClick={() => onSelectSession(session.id)}
              className={`
                w-full flex items-center gap-2 px-3 py-2.5 rounded-lg
                text-left text-sm transition-all duration-200 group
                ${
                  activeSessionId === session.id
                    ? "bg-white/10 text-white"
                    : "text-white/50 hover:text-white hover:bg-white/5"
                }
              `}
            >
              <MessageSquare size={14} className="shrink-0 opacity-60" />
              <span className="truncate">{session.title}</span>
            </button>
          ))}
        </div>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-white/5">
          <p className="text-white/20 text-xs">Business Intelligence AI</p>
        </div>
      </div>
    </>
  );
}

export default Sidebar;
