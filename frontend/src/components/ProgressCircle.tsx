import React from "react";

interface ProgressCircleProps {
  progress: number; // 0 - 100
  phase: string;
  position?: "left" | "right";
}

const phaseShortMap: Record<string, string> = {
  KYC: "KYC",
  BUSINESS_PLAN: "BP",
  ROADMAP: "RD",
  IMPLEMENTATION: "IMPL",
};

const ProgressCircle: React.FC<ProgressCircleProps> = ({
  progress,
  phase,
  position = "right",
}) => {
  const radius = 50;
  const stroke = 6;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  const positionClass =
    position === "right" ? "bottom-4 right-4" : "bottom-4 left-4";

  return (
    <div className={`fixed ${positionClass} z-50`}>
      <div className="relative w-[100px] h-[100px]">
        <svg
          height={radius * 2}
          width={radius * 2}
          className="text-gray-300 dark:text-gray-700"
        >
          <circle
            stroke="currentColor"
            fill="transparent"
            strokeWidth={stroke}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
          <circle
            stroke="currentColor"
            className="text-indigo-500 dark:text-indigo-400"
            fill="transparent"
            strokeWidth={stroke}
            strokeDasharray={`${circumference} ${circumference}`}
            style={{
              strokeDashoffset,
              transition: "stroke-dashoffset 0.35s",
            }}
            strokeLinecap="round"
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-1">
          <span className="text-base font-semibold text-indigo-600 dark:text-indigo-400">
            {Math.round(progress)}%
          </span>
          <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
            {phaseShortMap[phase] || phase}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ProgressCircle;
