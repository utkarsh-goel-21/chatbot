import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface AppUser {
  id: number;
  name: string;
  email: string;
}

const USERS: AppUser[] = [
  { id: 1, name: "Alice", email: "alice@bizbot.com" },
  { id: 2, name: "Bob", email: "bob@bizbot.com" },
];

const getRandomUser = (): AppUser => {
  return USERS[Math.floor(Math.random() * USERS.length)];
};

export interface Message {
  id: string;
  role: "user" | "ai";
  content: string;
  route?: "TEXT_TO_SQL" | "RAG";
  timestamp: number;
  isError?: boolean;
}

export interface Session {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: Message[];
}

interface AppStore {
  currentUser: AppUser;
  sessions: Session[];
  activeSessionId: string | null;
  isLoading: boolean;
  sidebarOpen: boolean;
  theme: "dark" | "light";
  toggleTheme: () => void;
  createSession: () => string;
  setActiveSession: (id: string) => void;
  deleteSession: (id: string) => void;
  addMessage: (sessionId: string, message: Message) => void;
  setLoading: (loading: boolean) => void;
  setSidebarOpen: (open: boolean) => void;
}

const genId = () => crypto.randomUUID();

export const useChatStore = create<AppStore>()(
  persist(
    (set, get) => ({
      currentUser: getRandomUser(),
      sessions: [],
      activeSessionId: null,
      isLoading: false,
      sidebarOpen: false,
      theme: "dark",
      toggleTheme: () => {
        const newTheme = get().theme === "dark" ? "light" : "dark";
        document.documentElement.className = newTheme;
        set({ theme: newTheme });
      },
      createSession: () => {
        const id = genId();
        const session: Session = {
          id,
          title: "New Conversation",
          createdAt: Date.now(),
          updatedAt: Date.now(),
          messages: [],
        };
        set((s) => ({
          sessions: [session, ...s.sessions],
          activeSessionId: id,
        }));
        return id;
      },
      setActiveSession: (id) => set({ activeSessionId: id }),
      deleteSession: (id) => {
        const state = get();
        const remaining = state.sessions.filter((s) => s.id !== id);
        if (remaining.length === 0) {
          const newId = genId();
          const session: Session = {
            id: newId,
            title: "New Conversation",
            createdAt: Date.now(),
            updatedAt: Date.now(),
            messages: [],
          };
          set({ sessions: [session], activeSessionId: newId });
        } else {
          set({
            sessions: remaining,
            activeSessionId:
              state.activeSessionId === id
                ? remaining[0].id
                : state.activeSessionId,
          });
        }
      },
      addMessage: (sessionId, message) => {
        set((s) => ({
          sessions: s.sessions.map((sess) => {
            if (sess.id !== sessionId) return sess;
            const msgs = [...sess.messages, message];
            const title =
              sess.title === "New Conversation" && message.role === "user"
                ? message.content.slice(0, 40) +
                  (message.content.length > 40 ? "…" : "")
                : sess.title;
            return { ...sess, messages: msgs, title, updatedAt: Date.now() };
          }),
        }));
      },
      setLoading: (loading) => set({ isLoading: loading }),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
    }),
    {
      name: "querymind_sessions",
      partialize: (state) => ({
        sessions: state.sessions,
        activeSessionId: state.activeSessionId,
        theme: state.theme,
      }),
    },
  ),
);

// Initialize on first load
const state = useChatStore.getState();
if (state.sessions.length === 0) {
  state.createSession();
} else if (!state.activeSessionId) {
  const sorted = [...state.sessions].sort((a, b) => b.updatedAt - a.updatedAt);
  state.setActiveSession(sorted[0].id);
}
