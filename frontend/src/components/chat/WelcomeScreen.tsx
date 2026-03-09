import DiamondIcon from "./DiamondIcon";

interface WelcomeScreenProps {
  onSuggestionClick: (text: string) => void;
}

const suggestions = [
  "How many sales did we make this week?",
  "Show me the top 5 products by revenue",
  "What were the transactions today?",
  "How has our business been performing?",
];

const WelcomeScreen = ({ onSuggestionClick }: WelcomeScreenProps) => (
  <div className="flex-1 flex flex-col items-center justify-center px-4">
    <DiamondIcon size={48} className="text-qm-green" />
    <h1 className="text-[28px] max-sm:text-[22px] font-bold text-qm-text mt-4">
      Ask anything about your data
    </h1>
    {/* <p className="text-[15px] text-qm-text-sec max-w-[420px] text-center mt-3 leading-relaxed">
      Powered by Text-to-SQL and RAG — get instant answers from your database and documents.
    </p> */}
    <div className="flex flex-wrap max-sm:flex-col items-center justify-center gap-3 mt-8">
      {suggestions.map((s) => (
        <button
          key={s}
          onClick={() => onSuggestionClick(s)}
          className="rounded-full border border-border px-[18px] py-2.5 text-sm text-qm-text-sec hover:border-qm-green hover:text-qm-text transition-all duration-150 cursor-pointer"
        >
          {s}
        </button>
      ))}
    </div>
  </div>
);

export default WelcomeScreen;
