import React from 'react';

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

interface HelpModalProps {
  isOpen: boolean;
  onClose: () => void;
  helpContent: string;
  task: ImplementationTask | null;
}

const HelpModal: React.FC<HelpModalProps> = ({
  isOpen,
  onClose,
  helpContent,
  task
}) => {
  if (!isOpen || !task) return null;

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

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-500 to-indigo-500 p-6 text-white rounded-t-xl">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">💡 Help & Guidance</h2>
              <p className="text-blue-100 mt-1">Expert assistance for {task.title}</p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-blue-200 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Task Overview */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-gray-900">{task.title}</h3>
              <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getPriorityColor(task.priority)}`}>
                {task.priority} Priority
              </span>
            </div>
            <p className="text-gray-700 text-sm mb-2">{task.description}</p>
            <div className="text-xs text-gray-500">
              <span className="font-medium">Phase:</span> {task.phase_name} • 
              <span className="font-medium ml-1">Estimated Time:</span> {task.estimated_time} • 
              <span className="font-medium ml-1">Business:</span> {task.business_context.business_name}
            </div>
          </div>

          {/* Help Content */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">📚 Detailed Guidance</h3>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="prose prose-sm max-w-none">
                <div className="whitespace-pre-wrap text-blue-800 font-sans leading-relaxed">
                  {helpContent}
                </div>
              </div>
            </div>
          </div>

          {/* Decision Options */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">🎯 Decision Options</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {task.options.map((option, index) => (
                <div key={index} className="bg-white border border-gray-200 rounded-lg p-3 hover:shadow-sm transition-shadow">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                      {index + 1}
                    </span>
                    <span className="text-gray-700">{option}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Angel Actions */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">✨ How Angel Can Help</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {task.angel_actions.map((action, index) => (
                <div key={index} className="bg-teal-50 border border-teal-200 rounded-lg p-3">
                  <div className="flex items-start gap-2">
                    <span className="text-teal-500 text-lg">✨</span>
                    <span className="text-teal-800 text-sm">{action}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Best Practices */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h3 className="font-semibold text-green-900 mb-2">🏆 Best Practices</h3>
            <div className="text-sm text-green-800 space-y-1">
              <p>• Research each option thoroughly before making a decision</p>
              <p>• Consider your business context and specific needs</p>
              <p>• Consult with experts or advisors when needed</p>
              <p>• Document your decision-making process</p>
              <p>• Review and adjust your approach as needed</p>
            </div>
          </div>

          {/* Common Pitfalls */}
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h3 className="font-semibold text-red-900 mb-2">⚠️ Common Pitfalls to Avoid</h3>
            <div className="text-sm text-red-800 space-y-1">
              <p>• Rushing into decisions without proper research</p>
              <p>• Choosing options based solely on cost</p>
              <p>• Ignoring legal and compliance requirements</p>
              <p>• Not considering long-term implications</p>
              <p>• Failing to document decisions and rationale</p>
            </div>
          </div>

          {/* Additional Resources */}
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <h3 className="font-semibold text-purple-900 mb-2">📖 Additional Resources</h3>
            <div className="text-sm text-purple-800 space-y-1">
              <p>• Government websites and official guidelines</p>
              <p>• Industry reports and market research</p>
              <p>• Professional associations and networks</p>
              <p>• Legal and financial advisory services</p>
              <p>• Peer networks and mentorship programs</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 rounded-b-xl flex justify-end">
          <button
            onClick={onClose}
            className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg font-medium transition-colors"
          >
            Got It!
          </button>
        </div>
      </div>
    </div>
  );
};

export default HelpModal;
