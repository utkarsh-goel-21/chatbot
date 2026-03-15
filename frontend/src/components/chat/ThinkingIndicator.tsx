import DiamondIcon from "./DiamondIcon";

const ThinkingIndicator = () => (
  <div className="flex items-start gap-3 animate-msg-in">
    <div className="mt-1 flex-shrink-0">
      <DiamondIcon size={16} className="text-qm-accent" />
    </div>
    <div className="bg-qm-elevated border border-border rounded-[18px_18px_18px_4px] p-4 max-w-[85%]">
      <div className="h-6 w-16 bg-qm-surface rounded-full mb-2.5 animate-pulse" />
      <div className="flex items-center gap-1.5">
        <span className="w-2 h-2 rounded-full bg-qm-green opacity-70 dot-bounce-1" />
        <span className="w-2 h-2 rounded-full bg-qm-green opacity-70 dot-bounce-2" />
        <span className="w-2 h-2 rounded-full bg-qm-green opacity-70 dot-bounce-3" />
      </div>
      <p className="text-qm-text-muted text-[13px] italic mt-2">
        Analyzing your question...
      </p>
    </div>
  </div>
);

export default ThinkingIndicator;
