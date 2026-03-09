import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import CodeBlock from "./CodeBlock";
import type { Components } from "react-markdown";

const components: Components = {
  code({ className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || "");
    const isInline = !match && !className;
    if (isInline) {
      return (
        <code
          className="bg-qm-elevated border border-border rounded px-1.5 py-0.5 font-mono text-[13px] text-qm-green"
          {...props}
        >
          {children}
        </code>
      );
    }
    return (
      <CodeBlock language={match?.[1] || ""}>
        {String(children).replace(/\n$/, "")}
      </CodeBlock>
    );
  },
  pre({ children }) {
    return <>{children}</>;
  },
  table({ children }) {
    return (
      <div className="overflow-x-auto my-4">
        <table className="w-full border-collapse">{children}</table>
      </div>
    );
  },
  thead({ children }) {
    return <thead>{children}</thead>;
  },
  th({ children }) {
    return (
      <th className="bg-qm-elevated text-qm-text font-semibold px-3.5 py-2.5 border-b-2 border-border text-left text-sm">
        {children}
      </th>
    );
  },
  td({ children }) {
    return (
      <td className="px-3.5 py-2.5 border-b border-border text-qm-text text-sm">
        {children}
      </td>
    );
  },
  tr({ children }) {
    return (
      <tr className="hover:bg-qm-elevated transition-colors">{children}</tr>
    );
  },
  blockquote({ children }) {
    return (
      <blockquote className="border-l-[3px] border-qm-green pl-3 text-qm-text-sec italic my-3">
        {children}
      </blockquote>
    );
  },
  p({ children }) {
    return (
      <p className="text-[15px] leading-[1.7] text-qm-text mb-3 last:mb-0">
        {children}
      </p>
    );
  },
  h1({ children }) {
    return (
      <h1 className="text-xl font-bold text-qm-text mt-4 mb-2">{children}</h1>
    );
  },
  h2({ children }) {
    return (
      <h2 className="text-[17px] font-bold text-qm-text mt-4 mb-2">
        {children}
      </h2>
    );
  },
  h3({ children }) {
    return (
      <h3 className="text-[15px] font-bold text-qm-text mt-4 mb-2">
        {children}
      </h3>
    );
  },
  ul({ children }) {
    return (
      <ul className="pl-5 list-disc text-qm-text mb-3 space-y-1">{children}</ul>
    );
  },
  ol({ children }) {
    return (
      <ol className="pl-5 list-decimal text-qm-text mb-3 space-y-1">
        {children}
      </ol>
    );
  },
  strong({ children }) {
    return <strong className="font-bold text-qm-text">{children}</strong>;
  },
  em({ children }) {
    return <em className="text-qm-text-sec">{children}</em>;
  },
};

const MarkdownRenderer = ({ content }: { content: string }) => (
  <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
    {content}
  </ReactMarkdown>
);

export default MarkdownRenderer;
