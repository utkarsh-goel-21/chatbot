import { useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useChatStore } from "@/store/chatStore";
import Sidebar from "@/components/chat/Sidebar";
import ChatArea from "@/components/chat/ChatArea";

const Index = () => {
  const { sidebarOpen, setSidebarOpen, theme } = useChatStore();

  useEffect(() => {
    document.documentElement.className = theme;
    const color = theme === "dark" ? "%23B86830" : "%23D4813A";
    const svg = `data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path d='M12 2L22 12L12 22L2 12Z' fill='${color}' opacity='0.3'/><path d='M12 2L22 12L12 22L2 12Z' stroke='${color}' stroke-width='1.5'/><path d='M12 7L17 12L12 17L7 12Z' fill='${color}'/></svg>`;
    const link = document.querySelector("link[rel='icon']") as HTMLLinkElement;
    if (link) link.href = svg;
  }, [theme]);

  return (
    <div className="flex h-screen w-full overflow-hidden">
      {/* Desktop sidebar */}
      <div className="hidden md:block w-[260px] flex-shrink-0">
        <Sidebar />
      </div>

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
