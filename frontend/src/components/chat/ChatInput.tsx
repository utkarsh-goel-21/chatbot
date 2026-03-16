import { useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import { ArrowUp, Loader2, Paperclip } from "lucide-react";

interface ChatInputProps {
  onSend: (text: string) => void;
  isLoading: boolean;
  inputRef?: React.RefObject<HTMLTextAreaElement | null>;
  onUpload?: (file: File) => void;
  isUploading?: boolean;
}

const ChatInput = ({
  onSend,
  isLoading,
  inputRef: externalRef,
  onUpload,
  isUploading,
}: ChatInputProps) => {
  const internalRef = useRef<HTMLTextAreaElement>(null);
  const ref = externalRef || internalRef;
  const csvInputRef = useRef<HTMLInputElement>(null);
  const docInputRef = useRef<HTMLInputElement>(null);
  const [showUploadMenu, setShowUploadMenu] = useState(false);
  const [showDemoPopup, setShowDemoPopup] = useState(false);

  const handleSend = () => {
    const val = ref.current?.value.trim();
    if (!val || isLoading) return;
    onSend(val);
    if (ref.current) {
      ref.current.value = "";
      ref.current.style.height = "auto";
    }
  };

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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onUpload) {
      onUpload(file);
      e.target.value = "";
    }
    setShowUploadMenu(false);
  };

  return (
    <div className="border-t border-border bg-qm-base px-6 max-sm:px-4 pt-4 pb-5">
      <div className="max-w-[760px] mx-auto">
        <div className="relative">
          {/* Upload menu popup */}
          {showUploadMenu && (
            <div className="absolute bottom-full mb-2 left-0 bg-qm-elevated border border-border rounded-xl shadow-lg overflow-hidden z-10">
              <button
                onClick={() => {
                  setShowUploadMenu(false);
                  setShowDemoPopup(true);
                }}
                className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-qm-text hover:bg-qm-surface transition-colors w-full text-left"
              >
                <span>📊</span>
                <span>Add CSV file</span>
              </button>
              <div className="border-t border-border" />
              <button
                onClick={() => {
                  setShowUploadMenu(false);
                  setShowDemoPopup(true);
                }}
                className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-qm-text hover:bg-qm-surface transition-colors w-full text-left"
              >
                <span>📄</span>
                <span>Add PDF / TXT file</span>
              </button>
            </div>
          )}

          {/* Demo account popup */}
          {showDemoPopup && (
            <div className="absolute bottom-full mb-2 left-0 bg-qm-elevated border border-border rounded-xl shadow-lg p-4 z-10 max-w-[280px]">
              <p className="text-sm text-qm-text font-medium mb-1">
                Demo Account
              </p>
              <p className="text-[13px] text-qm-text-sec leading-relaxed">
                File uploads are not available for demo accounts. Create an
                account to upload your own data.
              </p>
              <button
                onClick={() => setShowDemoPopup(false)}
                className="mt-3 w-full text-center text-[13px] text-qm-accent font-medium hover:opacity-80 transition-opacity"
              >
                Got it
              </button>
            </div>
          )}

          <div className="chat-input-box flex items-end gap-2.5 bg-qm-elevated border border-border rounded-2xl px-3.5 py-3 focus-within:border-qm-accent focus-within:shadow-[0_0_0_2px_rgba(212,129,58,0.15)] transition-all">
            {/* Hidden file inputs */}
            <input
              ref={csvInputRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={handleFileChange}
            />
            <input
              ref={docInputRef}
              type="file"
              accept=".pdf,.txt"
              className="hidden"
              onChange={handleFileChange}
            />

            {/* Paperclip button */}
            <button
              onClick={() => {
                setShowDemoPopup(false);
                setShowUploadMenu((v) => !v);
              }}
              disabled={isLoading || isUploading}
              className="flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-qm-text-muted hover:text-qm-text transition-colors disabled:opacity-50"
            >
              {isUploading ? (
                <Loader2 size={18} className="animate-spin text-qm-accent" />
              ) : (
                <Paperclip size={18} />
              )}
            </button>

            <textarea
              ref={ref}
              rows={1}
              placeholder="Ask anything about your data..."
              className="flex-1 bg-transparent border-none outline-none text-qm-text text-[15px] leading-[1.6] placeholder:text-qm-text-muted resize-none min-h-[24px] max-h-[200px] scrollbar-thin"
              onKeyDown={handleKeyDown}
              onInput={handleInput}
              onClick={() => {
                setShowUploadMenu(false);
                setShowDemoPopup(false);
              }}
            />

            <button
              onClick={handleSend}
              disabled={isLoading}
              className="flex-shrink-0 w-9 h-9 rounded-full bg-qm-accent flex items-center justify-center text-qm-base transition-all duration-150 hover:scale-105 hover:shadow-[0_0_16px_rgba(212,129,58,0.4)] active:scale-95 disabled:bg-qm-text-muted disabled:cursor-not-allowed disabled:shadow-none disabled:hover:scale-100"
            >
              {isLoading ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <ArrowUp size={18} />
              )}
            </button>
          </div>
        </div>
        <p className="text-qm-text-muted text-[11px] text-center mt-2.5">
          BizBot can make mistakes. Verify important data.
        </p>
      </div>
    </div>
  );
};

export default ChatInput;
