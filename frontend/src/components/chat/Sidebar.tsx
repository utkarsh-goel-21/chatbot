import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import {
  formatDistanceToNow,
  isToday,
  isYesterday,
  subDays,
  isAfter,
} from "date-fns";
import { useChatStore, type Session } from "@/store/chatStore";
import DiamondIcon from "./DiamondIcon";

function groupSessions(sessions: Session[]) {
  const today: Session[] = [];
  const yesterday: Session[] = [];
  const week: Session[] = [];
  const older: Session[] = [];
  const sevenDaysAgo = subDays(new Date(), 7);

  const sorted = [...sessions].sort((a, b) => b.updatedAt - a.updatedAt);
  for (const s of sorted) {
    const d = new Date(s.updatedAt);
    if (isToday(d)) today.push(s);
    else if (isYesterday(d)) yesterday.push(s);
    else if (isAfter(d, sevenDaysAgo)) week.push(s);
    else older.push(s);
  }
  return { today, yesterday, week, older };
}

const Sidebar = ({ onClose }: { onClose?: () => void }) => {
  const {
    sessions,
    activeSessionId,
    createSession,
    setActiveSession,
    deleteSession,
  } = useChatStore();
  const [confirmId, setConfirmId] = useState<string | null>(null);

  const handleNew = () => {
    createSession();
    onClose?.();
  };

  const handleSelect = (id: string) => {
    setActiveSession(id);
    onClose?.();
  };

  const groups = groupSessions(sessions);

  const renderGroup = (label: string, items: Session[]) => {
    if (items.length === 0) return null;
    return (
      <div key={label}>
        <p className="text-qm-text-muted text-[12px] uppercase font-semibold mt-4 mb-1 px-3">
          {label}
        </p>
        {items.map((s) => {
          const active = s.id === activeSessionId;
          return (
            <div
              key={s.id}
              onClick={() => handleSelect(s.id)}
              className={`group flex items-center h-10 rounded-xl px-3 cursor-pointer transition-all duration-150 ${
                active
                  ? "bg-qm-elevated border-l-2 border-qm-green text-qm-text"
                  : "text-qm-text-sec hover:bg-qm-elevated hover:text-qm-text"
              }`}
            >
              <span className="flex-1 text-sm truncate max-w-[160px]">
                {s.title.length > 28 ? s.title.slice(0, 28) + "…" : s.title}
              </span>
              {confirmId === s.id ? (
                <div
                  className="flex items-center gap-1 text-[11px]"
                  onClick={(e) => e.stopPropagation()}
                >
                  <span className="text-qm-text-sec">Delete?</span>
                  <button
                    onClick={() => {
                      deleteSession(s.id);
                      setConfirmId(null);
                    }}
                    className="text-red-400 hover:text-red-300 font-medium"
                  >
                    Yes
                  </button>
                  <button
                    onClick={() => setConfirmId(null)}
                    className="text-qm-text-sec hover:text-qm-text font-medium"
                  >
                    No
                  </button>
                </div>
              ) : (
                <>
                  <span className="text-qm-text-muted text-[11px] mr-1 group-hover:hidden">
                    {formatDistanceToNow(s.updatedAt, { addSuffix: false })}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setConfirmId(s.id);
                    }}
                    className="hidden group-hover:block text-qm-text-muted hover:text-red-400 transition-colors"
                  >
                    <Trash2 size={14} />
                  </button>
                </>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-qm-surface border-r border-border">
      {/* Top */}
      <div className="p-4 pb-3">
        <div className="flex items-center gap-2 mb-4">
          <DiamondIcon size={20} className="text-qm-green" />
          <span className="text-lg font-bold text-qm-text">BizBot</span>
        </div>
        <button
          onClick={handleNew}
          className="w-full flex items-center justify-center gap-2 rounded-full border border-qm-green text-qm-green py-2 text-sm font-medium hover:bg-qm-green hover:text-qm-base transition-all duration-150"
        >
          <Plus size={16} /> New Chat
        </button>
      </div>

      {/* Chat list */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-1">
        {renderGroup("Today", groups.today)}
        {renderGroup("Yesterday", groups.yesterday)}
        {renderGroup("Previous 7 Days", groups.week)}
        {renderGroup("Older", groups.older)}
      </div>

      {/* Bottom */}
      <div className="border-t border-border p-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-qm-elevated flex items-center justify-center">
            <DiamondIcon size={14} className="text-qm-green" />
          </div>
          <span className="flex-1 text-sm text-qm-text-sec">BizBot AI</span>
          <div className="w-2 h-2 rounded-full bg-qm-green" />
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
