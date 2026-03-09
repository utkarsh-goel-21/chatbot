import { useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Copy, Check } from "lucide-react";

interface CodeBlockProps {
  language?: string;
  children: string;
}

const customStyle = {
  ...atomDark,
  'pre[class*="language-"]': {
    ...atomDark['pre[class*="language-"]'],
    background: "#0D0F17",
    margin: 0,
    padding: "16px",
    fontSize: "13px",
    lineHeight: "1.6",
  },
  'code[class*="language-"]': {
    ...atomDark['code[class*="language-"]'],
    background: "transparent",
    fontSize: "13px",
    lineHeight: "1.6",
  },
};

const CodeBlock = ({ language = "", children }: CodeBlockProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl border border-border overflow-hidden my-3">
      <div className="h-9 flex items-center justify-between border-b border-border bg-qm-elevated px-3.5">
        <span className="text-xs font-semibold text-qm-text-sec">
          {language || "code"}
        </span>
        <button
          onClick={handleCopy}
          className="text-xs text-qm-text-sec hover:text-qm-text transition-colors flex items-center gap-1"
        >
          {copied ? (
            <>
              <Check size={12} className="text-qm-green" />{" "}
              <span className="text-qm-green">Copied ✓</span>
            </>
          ) : (
            <>
              <Copy size={12} /> Copy
            </>
          )}
        </button>
      </div>
      <SyntaxHighlighter
        language={language || "text"}
        style={customStyle}
        customStyle={{ background: "#0D0F17", margin: 0 }}
        wrapLongLines={false}
      >
        {children}
      </SyntaxHighlighter>
    </div>
  );
};

export default CodeBlock;
