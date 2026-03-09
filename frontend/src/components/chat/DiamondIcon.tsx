interface DiamondIconProps {
  size?: number;
  className?: string;
}

const DiamondIcon = ({ size = 24, className = "" }: DiamondIconProps) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    className={className}
  >
    <path d="M12 2L22 12L12 22L2 12L12 2Z" fill="currentColor" opacity="0.2" />
    <path
      d="M12 2L22 12L12 22L2 12L12 2Z"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinejoin="round"
    />
    <path d="M12 7L17 12L12 17L7 12L12 7Z" fill="currentColor" opacity="0.5" />
  </svg>
);

export default DiamondIcon;
