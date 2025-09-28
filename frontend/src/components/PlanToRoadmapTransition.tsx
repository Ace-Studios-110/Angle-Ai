import React, { useState } from 'react';
import { toast } from 'react-toastify';

interface PlanToRoadmapTransitionProps {
  businessPlanSummary: string;
  onApprove: () => void;
  onRevisit: (modificationAreas?: string[]) => void;
  loading?: boolean;
}

interface ModificationArea {
  id: string;
  title: string;
  description: string;
  questions: string[];
}

const PlanToRoadmapTransition: React.FC<PlanToRoadmapTransitionProps> = ({
  businessPlanSummary,
  onApprove,
  onRevisit,
  loading = false
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [showModificationModal, setShowModificationModal] = useState(false);
  const [selectedModifications, setSelectedModifications] = useState<string[]>([]);

  // Define modification areas based on business plan sections
  const modificationAreas: ModificationArea[] = [
    {
      id: 'business-overview',
      title: 'Business Overview',
      description: 'Core business concept, mission, vision, and value proposition',
      questions: [
        'Is your business concept clearly defined?',
        'Are your mission and vision statements compelling?',
        'Is your value proposition unique and marketable?'
      ]
    },
    {
      id: 'market-research',
      title: 'Market Research & Analysis',
      description: 'Target market, customer segments, and competitive landscape',
      questions: [
        'Have you thoroughly researched your target market?',
        'Are your customer personas detailed and accurate?',
        'Is your competitive analysis comprehensive?'
      ]
    },
    {
      id: 'financial-projections',
      title: 'Financial Projections',
      description: 'Revenue models, cost structure, and financial forecasts',
      questions: [
        'Are your revenue projections realistic?',
        'Have you accounted for all startup costs?',
        'Do you have a clear path to profitability?'
      ]
    },
    {
      id: 'operations',
      title: 'Operations & Logistics',
      description: 'Day-to-day operations, supply chain, and resource requirements',
      questions: [
        'Are your operational processes clearly defined?',
        'Have you identified key suppliers and partners?',
        'Is your resource planning complete?'
      ]
    },
    {
      id: 'marketing-strategy',
      title: 'Marketing & Sales Strategy',
      description: 'Customer acquisition, branding, and sales processes',
      questions: [
        'Is your marketing strategy comprehensive?',
        'Have you defined your sales process?',
        'Are your branding elements consistent?'
      ]
    },
    {
      id: 'legal-compliance',
      title: 'Legal & Compliance',
      description: 'Business structure, licenses, permits, and regulatory requirements',
      questions: [
        'Is your business structure optimal?',
        'Have you identified all required licenses?',
        'Are you compliant with regulations?'
      ]
    }
  ];

  const handleExportPlan = async () => {
    setIsExporting(true);
    try {
      // Create a downloadable text file with the business plan summary
      const element = document.createElement('a');
      const file = new Blob([businessPlanSummary], { type: 'text/plain' });
      element.href = URL.createObjectURL(file);
      element.download = 'business-plan-summary.txt';
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
      
      toast.success('Business plan summary exported successfully!');
    } catch (error) {
      toast.error('Failed to export business plan summary');
    } finally {
      setIsExporting(false);
    }
  };

  const handleRevisitClick = () => {
    setShowModificationModal(true);
  };

  const handleModificationToggle = (areaId: string) => {
    setSelectedModifications(prev => 
      prev.includes(areaId) 
        ? prev.filter(id => id !== areaId)
        : [...prev, areaId]
    );
  };

  const handleConfirmModifications = () => {
    if (selectedModifications.length === 0) {
      toast.warning('Please select at least one area to modify');
      return;
    }
    
    setShowModificationModal(false);
    onRevisit(selectedModifications);
    setSelectedModifications([]);
  };

  const handleCancelModifications = () => {
    setShowModificationModal(false);
    setSelectedModifications([]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-teal-50 flex items-center justify-center px-4">
      <div className="w-full max-w-4xl bg-white/90 backdrop-blur-xl border border-white/30 shadow-2xl rounded-3xl p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-20 h-20 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center text-white text-4xl mx-auto mb-4">
            🏆
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            🎉 CONGRATULATIONS! Planning Champion Award 🎉
          </h1>
          <p className="text-lg text-gray-600 mb-4">
            You've successfully completed your comprehensive business plan! This is a significant milestone in your entrepreneurial journey.
          </p>
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-4 mb-6">
            <blockquote className="text-lg font-medium text-blue-800 italic">
              "Success is not final; failure is not fatal: it is the courage to continue that counts."
            </blockquote>
            <cite className="text-sm text-blue-600 mt-2 block">– Winston Churchill</cite>
          </div>
        </div>

        {/* Business Plan Recap */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              📋 Comprehensive Business Plan Recap
            </h2>
            <button
              onClick={handleExportPlan}
              disabled={isExporting}
              className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center gap-2 disabled:opacity-50"
            >
              {isExporting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Exporting...
                </>
              ) : (
                <>
                  📄 Export Plan
                </>
              )}
            </button>
          </div>
          
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 max-h-96 overflow-y-auto">
            <div className="prose prose-sm max-w-none">
              <pre className="whitespace-pre-wrap text-gray-800 font-sans leading-relaxed">
                {businessPlanSummary}
              </pre>
            </div>
          </div>
        </div>

        {/* Contextual Reminders Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            🎯 Why This Roadmap Structure?
          </h2>
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-xl p-6">
            <p className="text-gray-700 mb-6">
              Each phase of your roadmap is strategically sequenced to build a strong foundation for your business. Here's why this order is crucial for your success:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                    1
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Legal Formation First</h3>
                    <p className="text-sm text-gray-600 mb-2">Business structure, licensing, permits</p>
                    <p className="text-xs text-gray-500">
                      <strong>Why first?</strong> Establishes your business foundation and protects your interests before any operations begin. 
                      This legal structure determines your tax obligations, liability protection, and business capabilities.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                    2
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Financial Planning Second</h3>
                    <p className="text-sm text-gray-600 mb-2">Funding strategies, budgeting, accounting setup</p>
                    <p className="text-xs text-gray-500">
                      <strong>Why second?</strong> Sets up your financial systems and funding strategies to support all subsequent operations. 
                      Without proper financial foundation, you can't effectively manage cash flow or secure necessary resources.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                    3
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Product & Operations Third</h3>
                    <p className="text-sm text-gray-600 mb-2">Supply chain, equipment, operational processes</p>
                    <p className="text-xs text-gray-500">
                      <strong>Why third?</strong> Builds your operational infrastructure once legal and financial foundations are secure. 
                      This ensures you can deliver your product or service efficiently and sustainably.
                    </p>
                  </div>
                </div>
              </div>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                    4
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Marketing & Sales Fourth</h3>
                    <p className="text-sm text-gray-600 mb-2">Brand positioning, customer acquisition, sales processes</p>
                    <p className="text-xs text-gray-500">
                      <strong>Why fourth?</strong> Promotes your business once all systems are in place and ready to handle customer demand. 
                      This prevents overwhelming your unprepared operations with too much demand too soon.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-teal-500 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                    5
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Full Launch & Scaling Last</h3>
                    <p className="text-sm text-gray-600 mb-2">Go-to-market strategy, growth planning</p>
                    <p className="text-xs text-gray-500">
                      <strong>Why last?</strong> Executes your complete business strategy when all foundational elements are ready. 
                      This systematic approach maximizes your chances of sustainable success and growth.
                    </p>
                  </div>
                </div>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-start gap-2">
                    <span className="text-yellow-600 text-sm">💡</span>
                    <div>
                      <h4 className="text-sm font-semibold text-yellow-800">Strategic Sequencing</h4>
                      <p className="text-xs text-yellow-700">
                        Each phase builds upon the previous one, creating a strong foundation that supports sustainable growth. 
                        Skipping or rushing phases can lead to costly mistakes and operational challenges.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* What's Next Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            🚀 What's Next: Roadmap Generation
          </h2>
          <div className="bg-gradient-to-r from-teal-50 to-blue-50 border border-teal-200 rounded-xl p-6">
            <p className="text-gray-700 mb-4">
              Based on your detailed business plan, I will now generate a comprehensive, actionable launch roadmap that translates your plan into explicit, chronological tasks. This roadmap will be:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="bg-white/50 rounded-lg p-4 border border-teal-200">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-teal-600">🔍</span>
                  <h3 className="font-semibold text-gray-900 text-sm">Research-Backed</h3>
                </div>
                <p className="text-xs text-gray-600">Based on authoritative sources and industry best practices</p>
              </div>
              <div className="bg-white/50 rounded-lg p-4 border border-teal-200">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-teal-600">📍</span>
                  <h3 className="font-semibold text-gray-900 text-sm">Location-Specific</h3>
                </div>
                <p className="text-xs text-gray-600">Tailored to your geographic location and regulations</p>
              </div>
              <div className="bg-white/50 rounded-lg p-4 border border-teal-200">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-teal-600">🎯</span>
                  <h3 className="font-semibold text-gray-900 text-sm">Industry-Focused</h3>
                </div>
                <p className="text-xs text-gray-600">Customized for your specific industry and business type</p>
              </div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-semibold text-blue-900 mb-2">📋 Roadmap Features Include:</h4>
              <ul className="text-blue-800 text-sm space-y-1">
                <li>• <strong>Actionable Tasks:</strong> Specific, executable steps with clear timelines</li>
                <li>• <strong>Decision Points:</strong> Multiple options presented for informed choices</li>
                <li>• <strong>Service Providers:</strong> Local and credible providers for each task</li>
                <li>• <strong>Resource Links:</strong> Government sites, industry reports, and authoritative sources</li>
                <li>• <strong>Progress Tracking:</strong> Clear milestones and completion indicators</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Decision Buttons */}
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            🚀 Ready to Move Forward?
          </h2>
          <p className="text-gray-600 mb-8">
            Please review your business plan summary above. If everything looks accurate and complete, you can:
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={onApprove}
              disabled={loading}
              className="group relative bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white px-8 py-4 rounded-xl text-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              <div className="flex items-center justify-center gap-3">
                <span className="text-xl">✅</span>
                <span>Approve Plan</span>
              </div>
              <div className="text-sm opacity-90 mt-1">Proceed to roadmap generation</div>
              <div className="absolute inset-0 bg-white/20 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            </button>

            <button
              onClick={handleRevisitClick}
              disabled={loading}
              className="group relative bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white px-8 py-4 rounded-xl text-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              <div className="flex items-center justify-center gap-3">
                <span className="text-xl">🔄</span>
                <span>Revisit Plan</span>
              </div>
              <div className="text-sm opacity-90 mt-1">Modify aspects that need adjustment</div>
              <div className="absolute inset-0 bg-white/20 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            </button>
          </div>
        </div>
      </div>

      {/* Modification Modal */}
      {showModificationModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Select Areas to Modify</h2>
              <p className="text-gray-600">
                Choose which sections of your business plan need adjustment. We'll guide you through the modification process for each selected area.
              </p>
            </div>

            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                {modificationAreas.map((area) => (
                  <div
                    key={area.id}
                    className={`border-2 rounded-lg p-4 cursor-pointer transition-all duration-200 ${
                      selectedModifications.includes(area.id)
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => handleModificationToggle(area.id)}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                        selectedModifications.includes(area.id)
                          ? 'border-blue-500 bg-blue-500'
                          : 'border-gray-300'
                      }`}>
                        {selectedModifications.includes(area.id) && (
                          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900 mb-1">{area.title}</h3>
                        <p className="text-sm text-gray-600 mb-2">{area.description}</p>
                        <div className="space-y-1">
                          {area.questions.map((question, index) => (
                            <p key={index} className="text-xs text-gray-500">• {question}</p>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {selectedModifications.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                  <h4 className="font-semibold text-blue-900 mb-2">Selected Areas:</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedModifications.map((areaId) => {
                      const area = modificationAreas.find(a => a.id === areaId);
                      return (
                        <span
                          key={areaId}
                          className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
                        >
                          {area?.title}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-3">
                <button
                  onClick={handleCancelModifications}
                  className="px-6 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmModifications}
                  className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
                >
                  Proceed with Modifications ({selectedModifications.length})
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PlanToRoadmapTransition;
