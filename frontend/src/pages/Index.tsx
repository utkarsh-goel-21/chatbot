import { useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useChatStore } from "@/store/chatStore";
import { supabase } from "@/lib/supabase";
import Sidebar from "@/components/chat/Sidebar";
import ChatArea from "@/components/chat/ChatArea";

const Index = () => {
  const { sidebarOpen, setSidebarOpen, isDesktopSidebarOpen, theme, setAuthUser } = useChatStore();

  useEffect(() => {
    document.documentElement.className = theme;
  }, [theme]);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setAuthUser(session?.user ?? null);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setAuthUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, [setAuthUser]);

  return (
    <div className="flex h-screen w-full overflow-hidden">
      {/* Desktop sidebar */}
      <AnimatePresence initial={false}>
        {isDesktopSidebarOpen && (
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: 260 }}
            exit={{ width: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="hidden md:block flex-shrink-0 overflow-hidden"
          >
            <div className="w-[260px] h-full">
              <Sidebar />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mobile sidebar drawer */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-40 md:hidden"
              onClick={() => setSidebarOpen(false)}
            />
            <motion.div
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="fixed left-0 top-0 bottom-0 w-[280px] z-50 md:hidden"
            >
              <Sidebar onClose={() => setSidebarOpen(false)} />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Chat area */}
      <ChatArea />
    </div>
  );
};

export default Index;
