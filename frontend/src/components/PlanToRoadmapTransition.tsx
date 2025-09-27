import React, { useState } from 'react';
import { toast } from 'react-toastify';

interface PlanToRoadmapTransitionProps {
  businessPlanSummary: string;
  onApprove: () => void;
  onRevisit: () => void;
  loading?: boolean;
}

const PlanToRoadmapTransition: React.FC<PlanToRoadmapTransitionProps> = ({
  businessPlanSummary,
  onApprove,
  onRevisit,
  loading = false
}) => {
  const [isExporting, setIsExporting] = useState(false);

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

        {/* What's Next Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            🎯 What's Next: Roadmap Generation
          </h2>
          <div className="bg-gradient-to-r from-teal-50 to-blue-50 border border-teal-200 rounded-xl p-6">
            <p className="text-gray-700 mb-4">
              Based on your detailed business plan, I will now generate a comprehensive, actionable launch roadmap that translates your plan into explicit, chronological tasks. This roadmap will include:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                  1
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Legal Formation</h3>
                  <p className="text-sm text-gray-600">Business structure, licensing, permits</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                  2
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Financial Planning</h3>
                  <p className="text-sm text-gray-600">Funding strategies, budgeting, accounting setup</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                  3
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Product & Operations</h3>
                  <p className="text-sm text-gray-600">Supply chain, equipment, operational processes</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                  4
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Marketing & Sales</h3>
                  <p className="text-sm text-gray-600">Brand positioning, customer acquisition, sales processes</p>
                </div>
              </div>
              <div className="flex items-start gap-3 md:col-span-2">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                  5
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Full Launch & Scaling</h3>
                  <p className="text-sm text-gray-600">Go-to-market strategy, growth planning</p>
                </div>
              </div>
            </div>
            <p className="text-gray-700 mt-4 text-sm">
              The roadmap will be tailored specifically to your business, industry, and location, with research-backed recommendations and local service provider options.
            </p>
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
              onClick={onRevisit}
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
    </div>
  );
};

export default PlanToRoadmapTransition;
