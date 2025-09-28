import React, { useState } from 'react';
import { toast } from 'react-toastify';

interface ImplementationTask {
  id: string;
  title: string;
  description: string;
  purpose: string;
  options: string[];
  angel_actions: string[];
  estimated_time: string;
  priority: string;
  phase_name: string;
  business_context: {
    business_name: string;
    industry: string;
    location: string;
    business_type: string;
  };
}

interface TaskCardProps {
  task: ImplementationTask;
  onComplete: () => void;
  onGetServiceProviders: () => void;
  onGetKickstart: () => void;
  onGetHelp: () => void;
  onUploadDocument: (file: File) => void;
}

const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onComplete,
  onGetServiceProviders,
  onGetKickstart,
  onGetHelp,
  onUploadDocument
}) => {
  const [selectedOption, setSelectedOption] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [dragActive, setDragActive] = useState(false);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onUploadDocument(file);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onUploadDocument(e.dataTransfer.files[0]);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getPhaseColor = (phase: string) => {
    switch (phase.toLowerCase()) {
      case 'legal formation & compliance':
        return 'bg-blue-500';
      case 'financial planning & setup':
        return 'bg-green-500';
      case 'product & operations development':
        return 'bg-purple-500';
      case 'marketing & sales strategy':
        return 'bg-orange-500';
      case 'full launch & scaling':
        return 'bg-teal-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="bg-white/90 backdrop-blur-xl border border-white/30 rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-teal-500 to-blue-500 p-6 text-white">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${getPhaseColor(task.phase_name)}`}></div>
            <span className="text-sm font-medium opacity-90">{task.phase_name}</span>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getPriorityColor(task.priority)}`}>
            {task.priority} Priority
          </span>
        </div>
        <h2 className="text-2xl font-bold mb-2">{task.title}</h2>
        <div className="flex items-center gap-4 text-sm opacity-90">
          <span>⏱️ {task.estimated_time}</span>
          <span>🎯 {task.angel_actions.length} Angel Actions</span>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Description */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Task Description</h3>
          <p className="text-gray-700 leading-relaxed">{task.description}</p>
        </div>

        {/* Purpose */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Why This Matters</h3>
          <p className="text-gray-700 leading-relaxed">{task.purpose}</p>
        </div>

        {/* Options */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Decision Options</h3>
          <div className="space-y-2">
            {task.options.map((option, index) => (
              <label key={index} className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                <input
                  type="radio"
                  name="option"
                  value={option}
                  checked={selectedOption === option}
                  onChange={(e) => setSelectedOption(e.target.value)}
                  className="w-4 h-4 text-teal-500 focus:ring-teal-500"
                />
                <span className="text-gray-700">{option}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Angel Actions */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">How Angel Can Help</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {task.angel_actions.map((action, index) => (
              <div key={index} className="flex items-center gap-3 p-3 bg-teal-50 border border-teal-200 rounded-lg">
                <span className="text-teal-500 text-lg">✨</span>
                <span className="text-gray-700 text-sm">{action}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Notes */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Additional Notes</h3>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add any additional notes or context for this task..."
            className="w-full p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent resize-none"
            rows={3}
          />
        </div>

        {/* Document Upload */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Upload Documents</h3>
          <div
            className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
              dragActive
                ? 'border-teal-500 bg-teal-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="text-gray-500">
              <svg className="mx-auto h-12 w-12 mb-4" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <p className="text-sm">
                <span className="font-medium text-teal-600 hover:text-teal-500 cursor-pointer">
                  Click to upload
                </span>
                {' '}or drag and drop
              </p>
              <p className="text-xs text-gray-400 mt-1">PDF, DOC, DOCX, JPEG, PNG up to 10MB</p>
            </div>
            <input
              type="file"
              onChange={handleFileUpload}
              className="hidden"
              id="file-upload"
              accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
            />
            <label htmlFor="file-upload" className="sr-only">Upload file</label>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-gray-200">
          <button
            onClick={onGetHelp}
            className="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-4 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
          >
            <span>💡</span>
            Get Help
          </button>
          <button
            onClick={onGetKickstart}
            className="flex-1 bg-green-500 hover:bg-green-600 text-white px-4 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
          >
            <span>🚀</span>
            Kickstart Plan
          </button>
          <button
            onClick={onGetServiceProviders}
            className="flex-1 bg-purple-500 hover:bg-purple-600 text-white px-4 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
          >
            <span>📞</span>
            Find Providers
          </button>
        </div>

        {/* Complete Task Button */}
        <div className="pt-4 border-t border-gray-200">
          <button
            onClick={onComplete}
            disabled={!selectedOption}
            className="w-full bg-teal-500 hover:bg-teal-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-6 py-4 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
          >
            <span>✅</span>
            Complete Task
          </button>
          {!selectedOption && (
            <p className="text-sm text-gray-500 mt-2 text-center">
              Please select a decision option to complete this task
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default TaskCard;
