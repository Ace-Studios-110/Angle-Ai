import React, { useState, useRef, useEffect } from 'react';
import SkillRatingForm from './SkillRatingForm';

interface SmartInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  loading?: boolean;
  currentQuestion?: string;
}

const SmartInput: React.FC<SmartInputProps> = ({
  value,
  onChange,
  onSubmit,
  placeholder = "Type your response...",
  disabled = false,
  loading = false,
  currentQuestion = ""
}) => {
  const [showRatingForm, setShowRatingForm] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Check if current question is about skill ratings
  useEffect(() => {
    const isSkillRatingQuestion = currentQuestion.includes('comfort') && 
                                 currentQuestion.includes('business skills') &&
                                 currentQuestion.includes('Rate each skill');
    setShowRatingForm(isSkillRatingQuestion);
  }, [currentQuestion]);

  const handleRatingSubmit = (ratings: number[]) => {
    const ratingString = ratings.join(', ');
    onChange(ratingString);
    onSubmit(ratingString);
    setShowRatingForm(false);
  };

  const handleRatingCancel = () => {
    setShowRatingForm(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit(value);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const target = e.target;
    onChange(target.value);
    
    // Auto-resize textarea
    target.style.height = "auto";
    target.style.height = Math.min(target.scrollHeight, 120) + "px";
  };

  if (showRatingForm) {
    return (
      <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow-lg border border-white/50 p-3">
        <SkillRatingForm
          onSubmit={handleRatingSubmit}
          onCancel={handleRatingCancel}
        />
      </div>
    );
  }

  return (
    <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow-lg border border-white/50 p-3">
      <div className="flex items-center gap-2 sm:gap-3">
        <div className="w-6 h-6 sm:w-7 sm:h-7 bg-gray-300 rounded-full flex items-center justify-center text-xs flex-shrink-0">
          👤
        </div>
        <div className="flex-1 min-w-0">
          <textarea
            ref={textareaRef}
            className="w-full rounded-lg p-2 sm:p-2.5 resize-none text-sm bg-gray-50 text-gray-900 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent focus:bg-white transition-all duration-200 placeholder-gray-500"
            rows={1}
            value={value}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            style={{ minHeight: "38px", maxHeight: "120px" }}
          />
        </div>
        <button
          className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white p-2 sm:p-2.5 rounded-lg font-medium text-sm disabled:opacity-50 shadow-md transition-all duration-200 flex-shrink-0"
          onClick={() => onSubmit(value)}
          disabled={loading || !value.trim()}
        >
          {loading ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
          ) : (
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
};

export default SmartInput;
