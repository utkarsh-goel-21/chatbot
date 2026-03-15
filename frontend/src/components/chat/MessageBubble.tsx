import { useState } from "react";
import { Copy, Check } from "lucide-react";
import { format } from "date-fns";
import type { Message } from "@/store/chatStore";
import RouteBadge from "./RouteBadge";
import MarkdownRenderer from "./MarkdownRenderer";
import DiamondIcon from "./DiamondIcon";

const MessageBubble = ({ message }: { message: Message }) => {
  const [copied, setCopied] = useState(false);
  const time = format(message.timestamp, "h:mm a");

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (message.role === "user") {
    return (
      <div className="flex justify-end animate-msg-in max-sm:pr-3">
        <div className="max-w-[70%] md:max-w-[70%] max-sm:max-w-[85%] max-sm:mr-2">
          <div
            className="rounded-[18px_18px_4px_18px] px-4 py-3 text-[15px] leading-[1.6] text-qm-text"
            style={{
              background: "var(--bg-message-user)",
              border: "1px solid var(--user-bubble-border)",
            }}
          >
            {message.content}
          </div>
          <p className="text-qm-text-muted text-[11px] text-right mt-1">
            {time}
          </p>
        </div>
      </div>
    );
  }

  const isError = message.isError;
  return (
    <div className="flex items-start gap-3 animate-msg-in  ">
      <div className="mt-1 flex-shrink-0 max-sm:ml-1">
        <DiamondIcon size={16} className="text-qm-accent" />
      </div>
      <div className="max-w-[85%] md:max-w-[85%] max-sm:max-w-[85%] max-sm:ml-1">
        <div
          className="rounded-[18px_18px_18px_4px] px-[18px] py-4"
          style={
            isError
              ? {
                  background: "var(--error-bg)",
                  border: "1px solid var(--error-border)",
                  color: "var(--error-text)",
                }
              : {
                  background: "var(--bg-message-ai)",
                  border: "1px solid var(--border-color)",
                }
          }
        >
          {!isError && message.route && (
            <div className="mb-2.5">
              <RouteBadge route={message.route} />
            </div>
          )}
          {isError ? (
            <p className="text-[15px] leading-[1.7]">{message.content}</p>
          ) : (
            <MarkdownRenderer content={message.content} />
          )}
        </div>
        <div className="flex items-center justify-between mt-1">
          <span className="text-qm-text-muted text-[11px]">{time}</span>
          <button
            onClick={handleCopy}
            className="text-qm-text-muted hover:text-qm-text transition-colors p-1"
          >
            {copied ? (
              <Check size={14} className="text-qm-green" />
            ) : (
              <Copy size={14} />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
