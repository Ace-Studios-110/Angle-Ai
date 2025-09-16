import React, { useState, useEffect } from 'react';
import { FaSearch, FaGlobe, FaLightbulb, FaChartLine } from 'react-icons/fa';

interface WebSearchIndicatorProps {
  isSearching: boolean;
  searchQuery?: string;
}

const WebSearchIndicator: React.FC<WebSearchIndicatorProps> = ({ isSearching, searchQuery }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [dots, setDots] = useState('');

  const steps = [
    { icon: FaSearch, text: 'Analyzing your request', color: 'text-blue-500' },
    { icon: FaGlobe, text: 'Searching the web', color: 'text-green-500' },
    { icon: FaChartLine, text: 'Processing data', color: 'text-purple-500' },
    { icon: FaLightbulb, text: 'Generating insights', color: 'text-yellow-500' }
  ];

  useEffect(() => {
    if (!isSearching) return;

    const interval = setInterval(() => {
      setCurrentStep(prev => (prev + 1) % steps.length);
    }, 1500);

    const dotsInterval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '' : prev + '.');
    }, 500);

    return () => {
      clearInterval(interval);
      clearInterval(dotsInterval);
    };
  }, [isSearching, steps.length]);

  if (!isSearching) return null;

  const CurrentIcon = steps[currentStep].icon;

  return (
    <div className="relative overflow-hidden bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 border border-blue-200 rounded-xl mb-6 shadow-lg">
      {/* Animated background */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-100/20 via-indigo-100/20 to-purple-100/20 animate-pulse"></div>
      
      <div className="relative p-6">
        {/* Header */}
        <div className="flex items-center justify-center mb-4">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center animate-pulse">
                <CurrentIcon className="text-white text-sm" />
              </div>
              <div className="absolute -inset-1 bg-blue-500 rounded-full opacity-20 animate-ping"></div>
            </div>
            <div className="text-center">
              <h3 className="text-lg font-bold text-gray-800">🔍 Research in Progress</h3>
              <p className="text-sm text-gray-600">Finding the best information for you</p>
            </div>
          </div>
        </div>

        {/* Progress steps */}
        <div className="flex justify-center space-x-4 mb-4">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isActive = index === currentStep;
            const isCompleted = index < currentStep;
            
            return (
              <div key={index} className="flex flex-col items-center space-y-2">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-500 ${
                  isActive 
                    ? 'bg-blue-500 scale-110 shadow-lg' 
                    : isCompleted 
                    ? 'bg-green-500' 
                    : 'bg-gray-300'
                }`}>
                  <Icon className={`text-sm ${
                    isActive || isCompleted ? 'text-white' : 'text-gray-500'
                  }`} />
                </div>
                <span className={`text-xs font-medium text-center max-w-20 ${
                  isActive ? 'text-blue-600' : isCompleted ? 'text-green-600' : 'text-gray-500'
                }`}>
                  {step.text}
                </span>
              </div>
            );
          })}
        </div>

        {/* Search query display */}
        {searchQuery && (
          <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 border border-blue-200">
            <div className="flex items-center space-x-2">
              <FaSearch className="text-blue-500 text-sm" />
              <span className="text-sm font-medium text-gray-700">Search Query:</span>
            </div>
            <div className="mt-2 p-3 bg-gray-50 rounded-md border-l-4 border-blue-400">
              <code className="text-sm text-gray-800 font-mono">"{searchQuery}"</code>
            </div>
          </div>
        )}

        {/* Animated progress bar */}
        <div className="mt-4">
          <div className="flex items-center justify-center space-x-2 text-sm text-gray-600">
            <span>Processing{dots}</span>
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          </div>
        </div>

        {/* Fun fact or tip */}
        <div className="mt-4 text-center">
          <div className="inline-flex items-center space-x-2 bg-yellow-50 border border-yellow-200 rounded-lg px-3 py-2">
            <FaLightbulb className="text-yellow-500 text-sm" />
            <span className="text-xs text-yellow-700 font-medium">
              💡 Did you know? Angel searches multiple sources to give you the most current information!
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WebSearchIndicator;
