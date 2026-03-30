import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@supabase/supabase-js";
export interface AppUser {
  id: number;
  name: string;
  email: string;
}

export const USERS: AppUser[] = [
  { id: 11091, name: "Dalton Perez", email: "dalton.perez@bizbot.com" },
  { id: 11176, name: "Mason Roberts", email: "mason.roberts@bizbot.com" },
];

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
  userId: string | number;
}

interface AppStore {
  currentUser: AppUser;
  sessions: Session[];
  activeSessionId: string | null;
  isLoading: boolean;
  sidebarOpen: boolean;
  authUser: User | null;
  theme: "dark" | "light";
  setCurrentUser: (user: AppUser) => void;
  setAuthUser: (user: User | null) => void;
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
      currentUser: USERS[0],
      sessions: [],
      activeSessionId: null,
      isLoading: false,
      sidebarOpen: false,
      authUser: null,
      theme: "dark",
      setCurrentUser: (user) => set({ currentUser: user }),
      setAuthUser: (user) => set({ authUser: user }),
      toggleTheme: () => {
        const newTheme = get().theme === "dark" ? "light" : "dark";
        document.documentElement.className = newTheme;
        set({ theme: newTheme });
      },
      createSession: () => {
        const id = genId();
        const state = get();
        const activeUserId = state.authUser?.id || state.currentUser.id;
        
        const session: Session = {
          id,
          title: "New Conversation",
          createdAt: Date.now(),
          updatedAt: Date.now(),
          messages: [],
          userId: activeUserId,
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
          const activeUserId = state.authUser?.id || state.currentUser.id;
          const session: Session = {
            id: newId,
            title: "New Conversation",
            createdAt: Date.now(),
            updatedAt: Date.now(),
            messages: [],
            userId: activeUserId,
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

// Initialize gracefully on load (will wipe old history missing userIds)
const state = useChatStore.getState();
const activeUserId = state.authUser?.id || state.currentUser.id;

// Filter out broken sessions from older versions without a userId
const validSessions = state.sessions.filter(s => s.userId);
if (validSessions.length !== state.sessions.length) {
    useChatStore.setState({ sessions: validSessions });
}

// Find sessions for active user
const userSessions = validSessions.filter((s) => s.userId === activeUserId);

if (userSessions.length === 0) {
  state.createSession();
} else if (!state.activeSessionId || !userSessions.find(s => s.id === state.activeSessionId)) {
  const sorted = [...userSessions].sort((a, b) => b.updatedAt - a.updatedAt);
  state.setActiveSession(sorted[0].id);
}
