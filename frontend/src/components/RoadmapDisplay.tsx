import React, { useState } from 'react';
import { toast } from 'react-toastify';

interface RoadmapDisplayProps {
  roadmapContent: string;
  onStartImplementation: () => void;
  onEditRoadmap?: (modifiedRoadmap: string) => void;
  loading?: boolean;
  sessionId?: string;
}

interface EditSection {
  id: string;
  title: string;
  content: string;
  type: 'phase' | 'task' | 'summary';
  phase?: string;
}

const RoadmapDisplay: React.FC<RoadmapDisplayProps> = ({
  roadmapContent,
  onStartImplementation,
  onEditRoadmap,
  loading = false,
  sessionId
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editSections, setEditSections] = useState<EditSection[]>([]);
  const [editingSection, setEditingSection] = useState<EditSection | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Parse roadmap content into editable sections
  const parseRoadmapSections = (content: string): EditSection[] => {
    const sections: EditSection[] = [];
    const lines = content.split('\n');
    let currentSection: EditSection | null = null;
    let sectionContent: string[] = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Check for phase headers (### 5. Phase X:)
      if (line.match(/^### \d+\. Phase \d+/)) {
        if (currentSection) {
          sections.push({
            ...currentSection,
            content: sectionContent.join('\n')
          });
        }
        currentSection = {
          id: `phase-${sections.length + 1}`,
          title: line.replace(/^### \d+\. /, ''),
          content: '',
          type: 'phase',
          phase: line.match(/Phase \d+/)?.[0]
        };
        sectionContent = [line];
      }
      // Check for task headers (#### Task X.X:)
      else if (line.match(/^#### Task \d+\.\d+/)) {
        if (currentSection) {
          sections.push({
            ...currentSection,
            content: sectionContent.join('\n')
          });
        }
        currentSection = {
          id: `task-${sections.length + 1}`,
          title: line.replace(/^#### /, ''),
          content: '',
          type: 'task',
          phase: sections[sections.length - 1]?.phase
        };
        sectionContent = [line];
      }
      // Check for summary sections (### X. Section)
      else if (line.match(/^### \d+\. [^P]/)) {
        if (currentSection) {
          sections.push({
            ...currentSection,
            content: sectionContent.join('\n')
          });
        }
        currentSection = {
          id: `summary-${sections.length + 1}`,
          title: line.replace(/^### \d+\. /, ''),
          content: '',
          type: 'summary'
        };
        sectionContent = [line];
      }
      else {
        sectionContent.push(line);
      }
    }

    // Add the last section
    if (currentSection) {
      sections.push({
        ...currentSection,
        content: sectionContent.join('\n')
      });
    }

    return sections;
  };

  const handleEditRoadmap = () => {
    const sections = parseRoadmapSections(roadmapContent);
    setEditSections(sections);
    setShowEditModal(true);
  };

  const handleSaveEdits = async () => {
    setIsSaving(true);
    try {
      // Reconstruct the roadmap with edited sections
      const modifiedContent = editSections
        .map(section => section.content)
        .join('\n\n');

      if (onEditRoadmap) {
        await onEditRoadmap(modifiedContent);
        toast.success('Roadmap updated successfully!');
        setShowEditModal(false);
      } else if (sessionId) {
        // If no onEditRoadmap callback, save directly to backend
        const response = await fetch(`/api/sessions/${sessionId}/modify-roadmap`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({ modified_content: modifiedContent })
        });

        if (response.ok) {
          toast.success('Roadmap updated successfully!');
          setShowEditModal(false);
        } else {
          throw new Error('Failed to save roadmap');
        }
      }
    } catch (error) {
      toast.error('Failed to save roadmap changes');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSectionEdit = (sectionId: string, newContent: string) => {
    setEditSections(prev => 
      prev.map(section => 
        section.id === sectionId 
          ? { ...section, content: newContent }
          : section
      )
    );
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Launch Roadmap</h1>
                <p className="text-gray-600">Your comprehensive business launch guide</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <button
                onClick={handleEditRoadmap}
                disabled={loading}
                className="px-4 py-2 bg-purple-100 hover:bg-purple-200 disabled:bg-gray-50 disabled:cursor-not-allowed text-purple-700 rounded-lg font-medium transition-colors duration-200 flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Edit Roadmap
              </button>
              <button
                onClick={handleExport}
                disabled={isExporting || loading}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 disabled:cursor-not-allowed text-gray-700 rounded-lg font-medium transition-colors duration-200 flex items-center gap-2"
              >
                {isExporting ? (
                  <>
                    <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Exporting...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Export
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Research Foundation Banner */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-lg p-6 mb-8 text-white">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h2 className="text-2xl font-bold">Research-Backed Launch Roadmap</h2>
              <p className="text-blue-100">Built on authoritative sources and industry best practices</p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-blue-200">🏛️</span>
              <span>Government Sources (SBA, SEC, IRS)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-blue-200">🎓</span>
              <span>Academic Research (Scholar, JSTOR)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-blue-200">📰</span>
              <span>Industry Reports (Forbes, HBR, Bloomberg)</span>
            </div>
          </div>
        </div>

        {/* Planning Champion Achievement */}
        <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-lg p-6 mb-8">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-16 h-16 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center text-white text-2xl">
              🏆
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Planning Champion Achievement</h2>
              <p className="text-gray-600">Congratulations on completing your comprehensive business planning!</p>
            </div>
          </div>
          <div className="bg-white/50 rounded-lg p-4 mb-4">
            <blockquote className="text-lg font-medium text-gray-800 italic mb-2">
              "Success is not final; failure is not fatal: it is the courage to continue that counts."
            </blockquote>
            <cite className="text-sm text-gray-600">– Winston Churchill</cite>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-green-600">✅</span>
              <span>Business Planning Complete</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-green-600">✅</span>
              <span>Market Research Done</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-green-600">✅</span>
              <span>Financial Strategy Set</span>
            </div>
          </div>
        </div>

        {/* Roadmap Content */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-8">
            <div className="prose prose-lg max-w-none">
              <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                {roadmapContent}
              </div>
            </div>
          </div>

          {/* Execution Excellence Section */}
          <div className="bg-gradient-to-r from-green-50 to-blue-50 border-t border-green-200 px-8 py-6">
            <div className="mb-6">
              <h3 className="text-xl font-bold text-gray-900 mb-3 flex items-center gap-2">
                <span className="text-2xl">🚀</span>
                Your Journey to Success
              </h3>
              <p className="text-gray-700 mb-4">
                This roadmap represents more than just tasks—it's your pathway to entrepreneurial success. Every element has been carefully researched and validated to help you build the business of your dreams.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white/50 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-2">Why Execution Matters:</h4>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>• <strong>Consistency:</strong> Don't miss critical steps</li>
                    <li>• <strong>Efficiency:</strong> Sequential approach prevents rework</li>
                    <li>• <strong>Confidence:</strong> Each phase builds momentum</li>
                    <li>• <strong>Success:</strong> 3x higher success rate with structured plans</li>
                  </ul>
                </div>
                <div className="bg-white/50 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-2">Your Success Commitment:</h4>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>• Dedicate time daily to roadmap tasks</li>
                    <li>• Use Angel's support whenever needed</li>
                    <li>• Stay flexible but maintain core sequence</li>
                    <li>• Celebrate milestones along the way</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="bg-gray-50 px-8 py-6 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                <p className="font-medium text-gray-900">Ready to begin your launch journey?</p>
                <p>Your roadmap is complete, researched, and ready for execution.</p>
                <p className="text-xs text-gray-500 mt-1">
                  This roadmap is tailored specifically to your business, industry, and location.
                </p>
              </div>
              
              <button
                onClick={onStartImplementation}
                disabled={loading}
                className="px-8 py-3 bg-gradient-to-r from-green-500 to-blue-600 hover:from-green-600 hover:to-blue-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-all duration-200 flex items-center gap-2 shadow-lg hover:shadow-xl transform hover:scale-105 disabled:transform-none"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Starting...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Start Implementation
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Enhanced Features Section */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-6 shadow-sm border border-green-200">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Research-Backed</h3>
            <p className="text-gray-600 text-sm">Built on authoritative sources including government agencies, academic institutions, and industry reports.</p>
          </div>

          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-6 shadow-sm border border-blue-200">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Actionable Tasks</h3>
            <p className="text-gray-600 text-sm">Each phase contains specific, executable tasks with clear timelines and decision points.</p>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-6 shadow-sm border border-purple-200">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Local Resources</h3>
            <p className="text-gray-600 text-sm">Provider tables include local service providers marked as "(Local)" for personalized support.</p>
          </div>

          <div className="bg-gradient-to-br from-orange-50 to-yellow-50 rounded-lg p-6 shadow-sm border border-orange-200">
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Execution Focus</h3>
            <p className="text-gray-600 text-sm">Designed to build the business of your dreams with proven methodologies and success metrics.</p>
          </div>
        </div>

        {/* Success Statistics */}
        <div className="mt-8 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-6 border border-indigo-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">Why This Roadmap Works</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
            <div>
              <div className="text-3xl font-bold text-indigo-600 mb-2">3x</div>
              <div className="text-sm text-gray-600">Higher success rate with structured launch plans</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-purple-600 mb-2">100%</div>
              <div className="text-sm text-gray-600">Research-backed recommendations from authoritative sources</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-600 mb-2">12</div>
              <div className="text-sm text-gray-600">Months of comprehensive guidance from planning to launch</div>
            </div>
          </div>
        </div>
      </div>

      {/* Edit Roadmap Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
            {/* Modal Header */}
            <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-blue-50">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Edit Roadmap</h2>
                  <p className="text-gray-600 mt-1">
                    Modify specific sections of your roadmap to better fit your needs
                  </p>
                </div>
                <button
                  onClick={() => setShowEditModal(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
              <div className="space-y-6">
                {editSections.map((section) => (
                  <div key={section.id} className="border border-gray-200 rounded-lg overflow-hidden">
                    {/* Section Header */}
                    <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white ${
                            section.type === 'phase' ? 'bg-blue-500' :
                            section.type === 'task' ? 'bg-green-500' : 'bg-purple-500'
                          }`}>
                            {section.type === 'phase' ? '📋' : section.type === 'task' ? '✅' : '📝'}
                          </div>
                          <div>
                            <h3 className="font-semibold text-gray-900">{section.title}</h3>
                            <p className="text-sm text-gray-600 capitalize">
                              {section.type} {section.phase && `• ${section.phase}`}
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => setEditingSection(editingSection?.id === section.id ? null : section)}
                          className="px-3 py-1 bg-purple-100 hover:bg-purple-200 text-purple-700 rounded-lg text-sm font-medium transition-colors"
                        >
                          {editingSection?.id === section.id ? 'Done' : 'Edit'}
                        </button>
                      </div>
                    </div>

                    {/* Section Content */}
                    <div className="p-4">
                      {editingSection?.id === section.id ? (
                        <textarea
                          value={section.content}
                          onChange={(e) => handleSectionEdit(section.id, e.target.value)}
                          className="w-full h-64 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                          placeholder="Edit this section..."
                        />
                      ) : (
                        <div className="prose prose-sm max-w-none">
                          <pre className="whitespace-pre-wrap text-gray-800 font-mono text-sm leading-relaxed">
                            {section.content}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  <p>💡 <strong>Tip:</strong> Click "Edit" on any section to modify its content</p>
                  <p>Your changes will be saved when you click "Save Changes"</p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setShowEditModal(false)}
                    className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveEdits}
                    disabled={isSaving}
                    className="px-6 py-2 bg-gradient-to-r from-purple-500 to-blue-600 hover:from-purple-600 hover:to-blue-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-all duration-200 flex items-center gap-2"
                  >
                    {isSaving ? (
                      <>
                        <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Saving...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        Save Changes
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RoadmapDisplay;
