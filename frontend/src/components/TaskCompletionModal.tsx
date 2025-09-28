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

interface TaskCompletionModalProps {
  isOpen: boolean;
  onClose: () => void;
  task: ImplementationTask | null;
  onComplete: (completionData: any) => void;
}

const TaskCompletionModal: React.FC<TaskCompletionModalProps> = ({
  isOpen,
  onClose,
  task,
  onComplete
}) => {
  const [decision, setDecision] = useState<string>('');
  const [actions, setActions] = useState<string>('');
  const [documents, setDocuments] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!task || !decision.trim()) {
      toast.error('Please provide the decision you made');
      return;
    }

    setLoading(true);
    
    const completionData = {
      decision: decision.trim(),
      actions: actions.trim(),
      documents: documents.trim(),
      notes: notes.trim()
    };

    try {
      await onComplete(completionData);
      // Reset form
      setDecision('');
      setActions('');
      setDocuments('');
      setNotes('');
    } catch (error) {
      console.error('Error completing task:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !task) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-500 to-teal-500 p-6 text-white rounded-t-xl">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">Complete Task</h2>
              <p className="text-green-100 mt-1">{task.title}</p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-green-200 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Task Summary */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">Task Summary</h3>
            <p className="text-gray-700 text-sm">{task.description}</p>
            <div className="mt-2 text-xs text-gray-500">
              <span className="font-medium">Phase:</span> {task.phase_name} • 
              <span className="font-medium ml-1">Priority:</span> {task.priority} • 
              <span className="font-medium ml-1">Estimated Time:</span> {task.estimated_time}
            </div>
          </div>

          {/* Decision Made */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              What decision did you make? *
            </label>
            <select
              value={decision}
              onChange={(e) => setDecision(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              required
            >
              <option value="">Select your decision...</option>
              {task.options.map((option, index) => (
                <option key={index} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          {/* Actions Taken */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              What actions did you take?
            </label>
            <textarea
              value={actions}
              onChange={(e) => setActions(e.target.value)}
              placeholder="Describe the specific actions you took to complete this task..."
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
              rows={3}
            />
          </div>

          {/* Documents Uploaded */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Documents uploaded (if any)
            </label>
            <textarea
              value={documents}
              onChange={(e) => setDocuments(e.target.value)}
              placeholder="List any documents you uploaded or created for this task..."
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
              rows={2}
            />
          </div>

          {/* Additional Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Additional notes or context
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Any additional information about how you completed this task..."
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
              rows={3}
            />
          </div>

          {/* Completion Checklist */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900 mb-2">Completion Checklist</h3>
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={decision.trim() !== ''}
                  readOnly
                  className="w-4 h-4 text-green-500 rounded focus:ring-green-500"
                />
                <span className={decision.trim() !== '' ? 'text-green-700' : 'text-gray-600'}>
                  Decision made and documented
                </span>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={actions.trim() !== ''}
                  readOnly
                  className="w-4 h-4 text-green-500 rounded focus:ring-green-500"
                />
                <span className={actions.trim() !== '' ? 'text-green-700' : 'text-gray-600'}>
                  Actions taken documented
                </span>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={true}
                  readOnly
                  className="w-4 h-4 text-green-500 rounded focus:ring-green-500"
                />
                <span className="text-green-700">
                  Task requirements met
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 rounded-b-xl flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !decision.trim()}
            className="bg-green-500 hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Completing...
              </>
            ) : (
              <>
                <span>✅</span>
                Complete Task
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default TaskCompletionModal;
