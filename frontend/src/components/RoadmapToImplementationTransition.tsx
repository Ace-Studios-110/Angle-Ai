import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';

interface RoadmapToImplementationTransitionProps {
  roadmapContent: string;
  onStartImplementation: () => void;
  loading?: boolean;
  sessionId?: string;
  businessContext?: {
    business_name: string;
    industry: string;
    location: string;
    business_type: string;
  };
}

interface MotivationalQuote {
  quote: string;
  author: string;
  category: string;
}

interface ServiceProviderPreview {
  name: string;
  type: string;
  local: boolean;
  description: string;
}

const RoadmapToImplementationTransition: React.FC<RoadmapToImplementationTransitionProps> = ({
  roadmapContent,
  onStartImplementation,
  loading = false,
  sessionId,
  businessContext
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [isLoadingProviders, setIsLoadingProviders] = useState(false);
  const [serviceProviderPreview, setServiceProviderPreview] = useState<ServiceProviderPreview[]>([]);
  const [motivationalQuote, setMotivationalQuote] = useState<MotivationalQuote>({
    quote: "Success is not final; failure is not fatal: it is the courage to continue that counts.",
    author: "Winston Churchill",
    category: "Persistence"
  });
  const [implementationInsights, setImplementationInsights] = useState<string>('');

  // Load service provider preview and implementation insights
  useEffect(() => {
    if (sessionId && businessContext) {
      loadImplementationPreparation();
    }
  }, [sessionId, businessContext]);

  const loadImplementationPreparation = async () => {
    setIsLoadingProviders(true);
    try {
      // Load service provider preview
      const providersResponse = await fetch(`${import.meta.env.VITE_API_BASE_URL}/implementation/sessions/${sessionId}/service-provider-preview`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('sb_access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (providersResponse.ok) {
        const providersData = await providersResponse.json();
        setServiceProviderPreview(providersData.providers || []);
      }

      // Load implementation insights
      const insightsResponse = await fetch(`${import.meta.env.VITE_API_BASE_URL}/implementation/sessions/${sessionId}/implementation-insights`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('sb_access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (insightsResponse.ok) {
        const insightsData = await insightsResponse.json();
        setImplementationInsights(insightsData.insights || '');
      }

      // Load motivational quote
      const quoteResponse = await fetch(`${import.meta.env.VITE_API_BASE_URL}/implementation/sessions/${sessionId}/motivational-quote`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('sb_access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (quoteResponse.ok) {
        const quoteData = await quoteResponse.json();
        setMotivationalQuote(quoteData.quote || motivationalQuote);
      }
    } catch (error) {
      console.error('Error loading implementation preparation:', error);
    } finally {
      setIsLoadingProviders(false);
    }
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      // Create a downloadable text file with the roadmap content
      const element = document.createElement('a');
      const file = new Blob([roadmapContent], { type: 'text/plain' });
      element.href = URL.createObjectURL(file);
      element.download = 'launch-roadmap.txt';
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
      
      toast.success('Roadmap exported successfully!');
    } catch (error) {
      toast.error('Failed to export roadmap');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-indigo-50 to-blue-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">From Planning to Action</h1>
              <p className="text-lg text-gray-600">The time has come to transition from planning into execution mode</p>
              <div className="mt-4 inline-flex items-center gap-2 bg-gradient-to-r from-purple-100 to-indigo-100 px-4 py-2 rounded-full">
                <span className="text-sm font-medium text-purple-800">🎯 Ready to Execute Your Vision</span>
              </div>
            </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Motivational Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden mb-8">
          <div className="bg-gradient-to-r from-purple-500 to-indigo-600 p-8 text-white">
            <div className="text-center">
              <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold mb-4">🚀 The Transition Moment</h2>
              <div className="bg-white/10 rounded-lg p-6 mb-6">
                <blockquote className="text-lg italic mb-4">
                  "{motivationalQuote.quote}"
                </blockquote>
                <p className="text-sm opacity-90">— {motivationalQuote.author}</p>
                <div className="text-xs opacity-75 mt-2">
                  Category: {motivationalQuote.category}
                </div>
              </div>
              <div className="bg-white/20 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-2">⚡ The Time Has Come</h3>
                <p className="text-sm opacity-95">
                  You've completed your planning phase. Now it's time to transition from strategic thinking into tactical execution. 
                  Every successful entrepreneur reaches this moment - the moment where plans become reality.
                </p>
              </div>
            </div>
          </div>
          
          <div className="p-8">
            <div className="prose prose-lg max-w-none">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">🎯 The Critical Transition: From Planning to Action</h3>
              
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6 mb-6">
                <h4 className="text-lg font-semibold text-blue-900 mb-3">✨ This Is Your Moment</h4>
                <p className="text-blue-800 mb-4">
                  Congratulations! You've successfully completed your comprehensive business plan and detailed launch roadmap{businessContext ? ` for "${businessContext.business_name}"` : ''}. 
                  <strong>The time has come to transition from planning into action.</strong> This is where your entrepreneurial journey 
                  truly begins to take shape.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white/50 rounded-lg p-4">
                    <h5 className="font-semibold text-blue-900 mb-2">📋 Planning Phase Complete</h5>
                    <ul className="text-sm text-blue-800 space-y-1">
                      <li>✅ Business plan finalized</li>
                      <li>✅ Launch roadmap created</li>
                      <li>✅ Research-backed strategy</li>
                      <li>✅ Action plan defined</li>
                    </ul>
                  </div>
                  <div className="bg-white/50 rounded-lg p-4">
                    <h5 className="font-semibold text-blue-900 mb-2">🚀 Implementation Phase Ready</h5>
                    <ul className="text-sm text-blue-800 space-y-1">
                      <li>🎯 Step-by-step execution</li>
                      <li>🔍 RAG-powered guidance</li>
                      <li>🤝 Service provider support</li>
                      <li>📈 Progress tracking</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Implementation Insights from RAG */}
              <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-6 mb-6">
                <h4 className="text-lg font-semibold text-indigo-900 mb-3 flex items-center gap-2">
                  <span>🧠</span>
                  <span>Research-Backed Implementation Insights</span>
                  <span className="text-xs bg-indigo-200 text-indigo-800 px-2 py-1 rounded-full">RAG-Powered</span>
                </h4>
                {implementationInsights ? (
                  <div className="text-indigo-800 whitespace-pre-wrap">
                    {implementationInsights}
                  </div>
                ) : (
                  <div className="text-indigo-700">
                    <p className="mb-3">
                      Throughout your implementation journey, Angel will utilize <strong>Retrieval Augmentation Generation (RAG) principles</strong> to provide you with the most accurate and up-to-date guidance.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-white/50 rounded-lg p-4">
                        <h5 className="font-semibold text-indigo-900 mb-2">🔍 Research Sources</h5>
                        <ul className="text-sm text-indigo-800 space-y-1">
                          <li>• Academic journals & research papers</li>
                          <li>• Government agencies (SBA, SEC, IRS)</li>
                          <li>• Educational institutions</li>
                          <li>• Reputable news sources</li>
                          <li>• Industry reports & publications</li>
                        </ul>
                      </div>
                      <div className="bg-white/50 rounded-lg p-4">
                        <h5 className="font-semibold text-indigo-900 mb-2">⚡ Real-Time Benefits</h5>
                        <ul className="text-sm text-indigo-800 space-y-1">
                          <li>• Evaluate accuracy of your answers</li>
                          <li>• Generate relevant service providers</li>
                          <li>• Provide informed mentorship</li>
                          <li>• Ensure compliance & best practices</li>
                          <li>• Access current industry standards</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
                <h4 className="text-lg font-semibold text-blue-900 mb-3">🚀 What's Next: Implementation Phase</h4>
                <p className="text-blue-800 mb-4">
                  The Implementation phase will guide you through executing each task step-by-step, turning your roadmap 
                  into actionable results. You'll receive:
                </p>
                <ul className="text-blue-800 space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></span>
                    <span><strong>Individual Task Guidance:</strong> Each task presented with detailed descriptions and clear purposes</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></span>
                    <span><strong>Multiple Decision Options:</strong> All relevant choices presented for informed decision-making</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></span>
                    <span><strong>Mentor Insights:</strong> Continuous support with research-backed guidance tailored to each step</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></span>
                    <span><strong>Flexible Navigation:</strong> Tasks presented one at a time with ability to revisit via navigation menu</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></span>
                    <span><strong>Dynamic Support:</strong> Interactive commands like "Help", "Kickstart", and "Who do I contact?"</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></span>
                    <span><strong>Service Provider Tables:</strong> Local and credible service providers for each step</span>
                  </li>
                </ul>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
                <h4 className="text-lg font-semibold text-green-900 mb-3">💡 How Angel Can Help You Execute</h4>
                <p className="text-green-800 mb-4">
                  Throughout implementation, Angel can assist you with:
                </p>
                <ul className="text-green-800 space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="w-2 h-2 bg-green-600 rounded-full mt-2 flex-shrink-0"></span>
                    <span>Reviewing and drafting contracts and legal documents</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-2 h-2 bg-green-600 rounded-full mt-2 flex-shrink-0"></span>
                    <span>Completing NDAs and other business documentation</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-2 h-2 bg-green-600 rounded-full mt-2 flex-shrink-0"></span>
                    <span>Analysis and research for business decisions</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-2 h-2 bg-green-600 rounded-full mt-2 flex-shrink-0"></span>
                    <span>Creating pitch decks and presentation materials</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-2 h-2 bg-green-600 rounded-full mt-2 flex-shrink-0"></span>
                    <span>Connecting you with local service providers</span>
                  </li>
                </ul>
              </div>

              {/* Service Provider Preview */}
              {(serviceProviderPreview.length > 0 || isLoadingProviders) && (
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-6 mb-6">
                  <h4 className="text-lg font-semibold text-orange-900 mb-3">🔗 Preview: Service Providers Ready for You</h4>
                  {isLoadingProviders ? (
                    <div className="flex items-center gap-2 text-orange-800">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-orange-600"></div>
                      <span>Loading service providers...</span>
                    </div>
                  ) : (
                    <>
                      <p className="text-orange-800 mb-4">
                        Based on your business context, here are some service providers we've identified to help you succeed:
                      </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {serviceProviderPreview.slice(0, 4).map((provider, index) => (
                      <div key={index} className="bg-white rounded-lg p-4 border border-orange-200">
                        <div className="flex items-start justify-between mb-2">
                          <h5 className="font-semibold text-gray-900">{provider.name}</h5>
                          {provider.local && (
                            <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                              (Local)
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{provider.type}</p>
                        <p className="text-xs text-gray-500">{provider.description}</p>
                      </div>
                    ))}
                  </div>
                      <p className="text-sm text-orange-700 mt-4">
                        💡 More providers will be available for each specific implementation task.
                      </p>
                    </>
                  )}
                </div>
              )}

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                <h4 className="text-lg font-semibold text-yellow-900 mb-3">⚠️ Important Implementation Notes</h4>
                <ul className="text-yellow-800 space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="w-2 h-2 bg-yellow-600 rounded-full mt-2 flex-shrink-0"></span>
                    <span>Every recommendation is grounded in deep research and designed to build your dream business</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-2 h-2 bg-yellow-600 rounded-full mt-2 flex-shrink-0"></span>
                    <span>You'll receive real-time feedback and suggestions as you complete each task</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-2 h-2 bg-yellow-600 rounded-full mt-2 flex-shrink-0"></span>
                    <span>Remember to declare task completions and upload relevant documentation</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-2 h-2 bg-yellow-600 rounded-full mt-2 flex-shrink-0"></span>
                    <span>Progress bars will track your completion throughout the implementation phase</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-2 h-2 bg-yellow-600 rounded-full mt-2 flex-shrink-0"></span>
                    <span>Local service providers are clearly marked and ready to assist you</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Business Context Summary */}
        {businessContext && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              Your Business Context
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Business Name</p>
                  <p className="font-semibold text-gray-900">{businessContext.business_name}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0H8m8 0v2a2 2 0 01-2 2H10a2 2 0 01-2-2V6m8 0H8" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Industry</p>
                  <p className="font-semibold text-gray-900">{businessContext.industry}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Location</p>
                  <p className="font-semibold text-gray-900">{businessContext.location}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Business Type</p>
                  <p className="font-semibold text-gray-900">{businessContext.business_type}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <div className="text-center mb-6">
            <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6 mb-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-3">🚀 The Moment Has Arrived</h3>
              <p className="text-lg text-gray-700 mb-4">
                <strong>The time has come to transition from planning into action.</strong> Your roadmap is complete and ready for execution. 
                The implementation phase will transform your plans into tangible results, guiding you through each step with expert support and local resources.
              </p>
              <div className="bg-white/50 rounded-lg p-4 mb-4">
                <p className="text-gray-800 font-medium">
                  "The way to get started is to quit talking and begin doing." - Walt Disney
                </p>
              </div>
              {businessContext && (
                <p className="text-sm text-gray-600">
                  This implementation process is tailored specifically to your "<strong>{businessContext.business_name}</strong>" business in the <strong>{businessContext.industry}</strong> industry, 
                  located in <strong>{businessContext.location}</strong>. Every recommendation is designed to help you build the business of your dreams.
                </p>
              )}
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={handleExport}
              disabled={isExporting || loading}
              className="px-6 py-3 bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 disabled:cursor-not-allowed text-gray-700 rounded-lg font-medium transition-colors duration-200 flex items-center gap-2"
            >
              {isExporting ? (
                <>
                  <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Exporting...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Export Roadmap
                </>
              )}
            </button>

            <button
              onClick={onStartImplementation}
              disabled={loading}
              className="px-10 py-4 bg-gradient-to-r from-green-500 to-blue-600 hover:from-green-600 hover:to-blue-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed text-white rounded-xl font-bold text-lg transition-all duration-200 flex items-center gap-3 shadow-xl hover:shadow-2xl transform hover:scale-105 disabled:transform-none"
            >
              {loading ? (
                <>
                  <svg className="animate-spin w-6 h-6" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Transitioning to Action...</span>
                </>
              ) : (
                <>
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span>Begin Implementation Journey</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Features Overview */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Step-by-Step Guidance</h3>
            <p className="text-gray-600 text-sm">Each task is presented individually with detailed descriptions and clear purposes.</p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Local Service Providers</h3>
            <p className="text-gray-600 text-sm">Provider tables with credible local service providers for each implementation step.</p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Dynamic Support</h3>
            <p className="text-gray-600 text-sm">Interactive commands and real-time feedback to guide you through each step.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RoadmapToImplementationTransition;
