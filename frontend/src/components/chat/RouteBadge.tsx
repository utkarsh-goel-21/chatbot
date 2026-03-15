import { Database, BookOpen } from "lucide-react";

interface RouteBadgeProps {
  route: "TEXT_TO_SQL" | "RAG";
}

const RouteBadge = ({ route }: RouteBadgeProps) => {
  const isSql = route === "TEXT_TO_SQL";
  return (
    <span
      className="inline-flex items-center gap-[5px] rounded-full px-[10px] text-[11px] font-semibold leading-6"
      style={{
        background: isSql ? "var(--sql-tag-bg)" : "var(--rag-tag-bg)",
        color: isSql ? "var(--sql-tag-text)" : "var(--rag-tag-text)",
        border: `1px solid ${isSql ? "var(--sql-tag-text)" : "var(--rag-tag-text)"}`,
      }}
    >
      {isSql ? <Database size={12} /> : <BookOpen size={12} />}
      {isSql ? "Text to SQL" : "Document Search"}
    </span>
  );
};

export default RouteBadge;
