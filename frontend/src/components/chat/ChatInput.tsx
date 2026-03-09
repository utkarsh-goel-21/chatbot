import { useRef, useCallback, KeyboardEvent } from "react";
import { ArrowUp, Loader2 } from "lucide-react";

interface ChatInputProps {
  onSend: (text: string) => void;
  isLoading: boolean;
  inputRef?: React.RefObject<HTMLTextAreaElement | null>;
}

const ChatInput = ({
  onSend,
  isLoading,
  inputRef: externalRef,
}: ChatInputProps) => {
  const internalRef = useRef<HTMLTextAreaElement>(null);
  const ref = externalRef || internalRef;

  const handleSend = useCallback(() => {
    const val = ref.current?.value.trim();
    if (!val || isLoading) return;
    onSend(val);
    if (ref.current) {
      ref.current.value = "";
      ref.current.style.height = "auto";
    }
  }, [onSend, isLoading, ref]);

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  };

  return (
    <div className="border-t border-border bg-qm-base px-6 max-sm:px-4 pt-4 pb-5">
      <div className="max-w-[760px] mx-auto">
        <div className="flex items-end gap-2.5 bg-qm-elevated border border-border rounded-2xl px-3.5 py-3 focus-within:border-qm-green focus-within:shadow-[0_0_0_2px_rgba(0,255,163,0.15)] transition-all">
          <textarea
            ref={ref}
            rows={1}
            placeholder="Ask anything about your data..."
            className="flex-1 bg-transparent border-none outline-none text-qm-text text-[15px] leading-[1.6] placeholder:text-qm-text-muted resize-none min-h-[24px] max-h-[200px] scrollbar-thin"
            onKeyDown={handleKeyDown}
            onInput={handleInput}
          />
          <button
            onClick={handleSend}
            disabled={isLoading}
            className="flex-shrink-0 w-9 h-9 rounded-full bg-qm-green flex items-center justify-center text-qm-base transition-all duration-150 hover:scale-105 hover:shadow-[0_0_16px_rgba(0,255,163,0.4)] active:scale-95 disabled:bg-qm-text-muted disabled:cursor-not-allowed disabled:shadow-none disabled:hover:scale-100"
          >
            {isLoading ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <ArrowUp size={18} />
            )}
          </button>
        </div>
        <p className="text-qm-text-muted text-[11px] text-center mt-2.5">
          BizBot can make mistakes. Verify important data.
        </p>
      </div>
    </div>
  );
};

export default ChatInput;
