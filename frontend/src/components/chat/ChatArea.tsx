import { useRef, useEffect, useCallback, useState, useMemo } from "react";
import { Menu } from "lucide-react";
import { useChatStore } from "@/store/chatStore";
import { sendChatMessage, uploadFile } from "@/lib/api";
import MessageBubble from "./MessageBubble";
import ThinkingIndicator from "./ThinkingIndicator";
import WelcomeScreen from "./WelcomeScreen";
import ChatInput from "./ChatInput";
import AuthModal from "@/components/auth/AuthModal";

const ChatArea = () => {
  const {
    sessions,
    activeSessionId,
    isLoading,
    createSession,
    addMessage,
    setLoading,
    setSidebarOpen,
    currentUser,
    authUser,
  } = useChatStore();

  const activeSession = sessions.find((s) => s.id === activeSessionId);
  const messages = useMemo(
    () => activeSession?.messages || [],
    [activeSession],
  );
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [signupMode, setSignupMode] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages.length, isLoading]);

  const handleSend = useCallback(
    async (text: string) => {
      let sessionId = activeSessionId;
      if (!sessionId) {
        sessionId = createSession();
      }

      const userMsg = {
        id: crypto.randomUUID(),
        role: "user" as const,
        content: text,
        timestamp: Date.now(),
      };
      addMessage(sessionId, userMsg);
      setLoading(true);

      try {
        const res = await sendChatMessage(
          text,
          currentUser.id,
          messages.map((m) => ({ role: m.role, content: m.content })),
        );
        addMessage(sessionId, {
          id: crypto.randomUUID(),
          role: "ai",
          content: res.answer,
          route: res.route,
          timestamp: Date.now(),
        });
      } catch {
        addMessage(sessionId, {
          id: crypto.randomUUID(),
          role: "ai",
          content:
            "Sorry, I couldn't reach the server. Make sure the backend is running at http://127.0.0.1:8000 and try again.",
          timestamp: Date.now(),
          isError: true,
        });
      } finally {
        setLoading(false);
      }
    },
    [
      activeSessionId,
      addMessage,
      createSession,
      setLoading,
      currentUser,
      messages,
    ],
  );

  const handleUpload = async (file: File) => {
    let sessionId = activeSessionId;
    if (!sessionId) {
      sessionId = createSession();
    }
    setIsUploading(true);
    try {
      const res = await uploadFile(file, currentUser.id);
      addMessage(sessionId, {
        id: crypto.randomUUID(),
        role: "ai",
        content: res.message,
        timestamp: Date.now(),
      });
    } catch {
      addMessage(sessionId, {
        id: crypto.randomUUID(),
        role: "ai",
        content: "Sorry, file upload failed. Please try again.",
        timestamp: Date.now(),
        isError: true,
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleSuggestion = (text: string) => {
    handleSend(text);
  };

  const title = activeSession?.title || "New Conversation";

  return (
    <div className="flex-1 flex flex-col h-screen bg-qm-base">
      {/* Header */}
      <div className="h-14 flex items-center justify-between px-6 max-sm:px-4 border-b border-border flex-shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(true)}
            className="md:hidden text-qm-text-sec hover:text-qm-text transition-colors max-sm:ml-1"
          >
            <Menu size={20} />
          </button>
          <h2 className="font-semibold text-qm-text text-sm truncate max-w-[300px] max-sm:max-w-[160px]">
            {title}
          </h2>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-qm-text-muted text-[13px]">
            {messages.length} messages
          </span>
          {!authUser && (
            <div className="hidden md:flex items-center gap-2">
              <button
                onClick={() => {
                  setSignupMode(false);
                  setShowAuthModal(true);
                }}
                className="text-sm text-qm-text border border-border rounded-lg px-3 py-1.5 hover:bg-qm-elevated transition-colors"
              >
                Log in
              </button>
              <button
                onClick={() => {
                  setSignupMode(true);
                  setShowAuthModal(true);
                }}
                className="text-sm text-qm-base bg-qm-accent rounded-lg px-3 py-1.5 hover:opacity-90 transition-opacity font-medium"
              >
                Sign up
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Messages */}
      {messages.length === 0 && !isLoading ? (
        <WelcomeScreen onSuggestionClick={handleSuggestion} />
      ) : (
        <div className="flex-1 overflow-y-auto scrollbar-thin px-6 max-sm:px-5 py-6">
          <div className="max-w-[760px] mx-auto space-y-6">
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
            {isLoading && <ThinkingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        isLoading={isLoading}
        inputRef={inputRef}
        onUpload={handleUpload}
        isUploading={isUploading}
      />

      {/* Auth Modal */}
      {showAuthModal && (
        <AuthModal
          defaultMode={signupMode ? "signup" : "login"}
          onClose={() => {
            setShowAuthModal(false);
            setSignupMode(false);
          }}
        />
      )}
    </div>
  );
};

export default ChatArea;
