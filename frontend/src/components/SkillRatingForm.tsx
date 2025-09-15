import React, { useState } from 'react';
import SkillRating from './SkillRating';

interface SkillRatingFormProps {
  onSubmit: (ratings: number[]) => void;
  onCancel: () => void;
}

const skills = [
  { name: 'Business Planning', emoji: '📋' },
  { name: 'Financial Modeling', emoji: '💰' },
  { name: 'Legal Formation', emoji: '⚖️' },
  { name: 'Marketing', emoji: '📢' },
  { name: 'Operations/Logistics', emoji: '🚚' },
  { name: 'Technology/Infrastructure', emoji: '💻' },
  { name: 'Fundraising/Investor Outreach', emoji: '💼' },
];

const SkillRatingForm: React.FC<SkillRatingFormProps> = ({ onSubmit, onCancel }) => {
  const [ratings, setRatings] = useState<number[]>([0, 0, 0, 0, 0, 0, 0]);
  const [isComplete, setIsComplete] = useState(false);

  const handleRatingChange = (index: number, value: number) => {
    const newRatings = [...ratings];
    newRatings[index] = value;
    setRatings(newRatings);
    
    // Check if all ratings are complete
    const allRated = newRatings.every(rating => rating > 0);
    setIsComplete(allRated);
  };

  const handleSubmit = () => {
    if (isComplete) {
      onSubmit(ratings);
    }
  };

  const completedCount = ratings.filter(rating => rating > 0).length;

  return (
    <div className="bg-gradient-to-br from-slate-50 to-teal-50 rounded-xl p-6 shadow-lg border border-white/50">
      {/* Header */}
      <div className="text-center mb-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2">
          Rate Your Business Skills
        </h3>
        <p className="text-gray-600 text-sm">
          How comfortable are you with these business skills? Rate each from 1 to 5.
        </p>
        <div className="mt-3">
          <div className="flex items-center justify-center gap-2">
            <div className="w-32 bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-teal-500 to-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(completedCount / 7) * 100}%` }}
              ></div>
            </div>
            <span className="text-sm text-gray-600 font-medium">
              {completedCount}/7 completed
            </span>
          </div>
        </div>
      </div>

      {/* Skills Rating */}
      <div className="space-y-3 mb-6">
        {skills.map((skill, index) => (
          <SkillRating
            key={index}
            skill={skill.name}
            emoji={skill.emoji}
            value={ratings[index]}
            onChange={(value) => handleRatingChange(index, value)}
          />
        ))}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 justify-center">
        <button
          onClick={onCancel}
          className="px-6 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={!isComplete}
          className={`
            px-6 py-2 rounded-lg font-medium transition-all duration-200
            ${isComplete 
              ? 'bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white shadow-md hover:shadow-lg transform hover:scale-105' 
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }
          `}
        >
          {isComplete ? 'Submit Ratings' : 'Complete All Ratings'}
        </button>
      </div>

      {/* Quick Fill Options */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500 text-center mb-2">Quick fill options:</p>
        <div className="flex gap-2 justify-center">
          {[1, 2, 3, 4, 5].map((rating) => (
            <button
              key={rating}
              onClick={() => setRatings([rating, rating, rating, rating, rating, rating, rating])}
              className="px-3 py-1 text-xs bg-gray-100 hover:bg-teal-100 text-gray-600 hover:text-teal-700 rounded-md transition-colors"
            >
              All {rating}s
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SkillRatingForm;
