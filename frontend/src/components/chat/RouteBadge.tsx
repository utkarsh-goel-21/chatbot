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
        background: isSql ? "#3B82F620" : "#9945FF20",
        color: isSql ? "#3B82F6" : "#9945FF",
        border: `1px solid ${isSql ? "#3B82F640" : "#9945FF40"}`,
      }}
    >
      {isSql ? <Database size={12} /> : <BookOpen size={12} />}
      {isSql ? "Text to SQL" : "Document Search"}
    </span>
  );
};

export default RouteBadge;
