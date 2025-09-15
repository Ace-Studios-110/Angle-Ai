import React, { useState } from 'react';

interface SkillRatingProps {
  skill: string;
  emoji: string;
  value: number;
  onChange: (value: number) => void;
}

const SkillRating: React.FC<SkillRatingProps> = ({ skill, emoji, value, onChange }) => {
  const [hoveredRating, setHoveredRating] = useState<number | null>(null);

  const handleRatingClick = (rating: number) => {
    onChange(rating);
  };

  const handleMouseEnter = (rating: number) => {
    setHoveredRating(rating);
  };

  const handleMouseLeave = () => {
    setHoveredRating(null);
  };

  return (
    <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100 mb-3">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{emoji}</span>
          <span className="font-semibold text-gray-800">{skill}</span>
        </div>
        <div className="text-sm text-gray-500">
          {value > 0 ? `${value}/5` : 'Rate this skill'}
        </div>
      </div>
      
      <div className="flex items-center gap-2">
        {[1, 2, 3, 4, 5].map((rating) => {
          const isActive = rating <= (hoveredRating || value);
          const isSelected = rating === value;
          
          return (
            <button
              key={rating}
              onClick={() => handleRatingClick(rating)}
              onMouseEnter={() => handleMouseEnter(rating)}
              onMouseLeave={handleMouseLeave}
              className={`
                w-10 h-10 rounded-full border-2 transition-all duration-200 flex items-center justify-center text-sm font-medium
                ${isActive 
                  ? 'bg-gradient-to-r from-teal-500 to-blue-500 text-white border-teal-500 shadow-md' 
                  : 'bg-gray-50 text-gray-400 border-gray-200 hover:border-teal-300 hover:bg-teal-50'
                }
                ${isSelected ? 'ring-2 ring-teal-300 ring-offset-2' : ''}
                hover:scale-110 transform
              `}
            >
              {rating}
            </button>
          );
        })}
      </div>
      
      <div className="mt-2 text-xs text-gray-500">
        {value === 1 && 'Not comfortable at all'}
        {value === 2 && 'Slightly uncomfortable'}
        {value === 3 && 'Somewhat comfortable'}
        {value === 4 && 'Quite comfortable'}
        {value === 5 && 'Very comfortable'}
      </div>
    </div>
  );
};

export default SkillRating;
