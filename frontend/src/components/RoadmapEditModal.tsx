import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';

interface RoadmapEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  roadmapContent: string;
  sessionId: string;
  onSave: (updatedContent: string) => void;
  loading?: boolean;
}

interface RoadmapSection {
  id: string;
  title: string;
  content: string;
  phase: string;
  editable: boolean;
}

const RoadmapEditModal: React.FC<RoadmapEditModalProps> = ({
  isOpen,
  onClose,
  roadmapContent,
  sessionId,
  onSave,
  loading = false
}) => {
  const [sections, setSections] = useState<RoadmapSection[]>([]);
  const [editingSection, setEditingSection] = useState<string | null>(null);
  const [editContent, setEditContent] = useState<string>('');
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Parse roadmap content into sections
  useEffect(() => {
    if (roadmapContent && isOpen) {
      parseRoadmapContent(roadmapContent);
    }
  }, [roadmapContent, isOpen]);

  const parseRoadmapContent = (content: string) => {
    const lines = content.split('\n');
    const parsedSections: RoadmapSection[] = [];
    let currentSection: RoadmapSection | null = null;
    let sectionContent: string[] = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      // Check for phase headers (Phase 1:, Phase 2:, etc.)
      if (line.match(/^Phase \d+:/i)) {
        // Save previous section if exists
        if (currentSection) {
          currentSection.content = sectionContent.join('\n');
          parsedSections.push(currentSection);
        }
        
        // Start new section
        const phaseMatch = line.match(/^Phase (\d+):\s*(.+)/i);
        if (phaseMatch) {
          currentSection = {
            id: `phase-${phaseMatch[1]}`,
            title: phaseMatch[2] || `Phase ${phaseMatch[1]}`,
            content: '',
            phase: `Phase ${phaseMatch[1]}`,
            editable: true
          };
          sectionContent = [];
        }
      } else if (line.match(/^[A-Z][^:]*:$/)) {
        // Check for subsection headers
        if (currentSection) {
          sectionContent.push(line);
        }
      } else if (line.length > 0) {
        // Regular content
        if (currentSection) {
          sectionContent.push(line);
        }
      }
    }

    // Save last section
    if (currentSection) {
      currentSection.content = sectionContent.join('\n');
      parsedSections.push(currentSection);
    }

    // If no sections found, create a single editable section
    if (parsedSections.length === 0) {
      parsedSections.push({
        id: 'full-roadmap',
        title: 'Complete Roadmap',
        content: content,
        phase: 'All Phases',
        editable: true
      });
    }

    setSections(parsedSections);
  };

  const handleEditSection = (sectionId: string) => {
    const section = sections.find(s => s.id === sectionId);
    if (section) {
      setEditingSection(sectionId);
      setEditContent(section.content);
    }
  };

  const handleSaveSection = () => {
    if (!editingSection) return;

    setSections(prev => prev.map(section => 
      section.id === editingSection 
        ? { ...section, content: editContent }
        : section
    ));
    setEditingSection(null);
    setEditContent('');
    setHasChanges(true);
    toast.success('Section updated successfully!');
  };

  const handleCancelEdit = () => {
    setEditingSection(null);
    setEditContent('');
  };

  const handleSaveRoadmap = async () => {
    setIsSaving(true);
    try {
      // Reconstruct the full roadmap content
      const updatedContent = sections.map(section => 
        `${section.phase}: ${section.title}\n\n${section.content}`
      ).join('\n\n---\n\n');

      await onSave(updatedContent);
      setHasChanges(false);
      toast.success('Roadmap saved successfully!');
    } catch (error) {
      console.error('Error saving roadmap:', error);
      toast.error('Failed to save roadmap');
    } finally {
      setIsSaving(false);
    }
  };

  const handleRegenerateSection = async (sectionId: string) => {
    const section = sections.find(s => s.id === sectionId);
    if (!section) return;

    try {
      toast.info(`Regenerating ${section.title}...`);
      
      // Call API to regenerate specific section
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/angel/sessions/${sessionId}/regenerate-roadmap-section`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          section_id: sectionId,
          section_title: section.title,
          current_content: section.content
        })
      });

      if (!response.ok) {
        throw new Error('Failed to regenerate section');
      }

      const data = await response.json();
      
      if (data.success) {
        setSections(prev => prev.map(s => 
          s.id === sectionId 
            ? { ...s, content: data.regenerated_content }
            : s
        ));
        setHasChanges(true);
        toast.success(`${section.title} regenerated successfully!`);
      } else {
        toast.error(data.message || 'Failed to regenerate section');
      }
    } catch (error) {
      console.error('Error regenerating section:', error);
      toast.error('Failed to regenerate section');
    }
  };

  const handleAddSection = () => {
    const newSection: RoadmapSection = {
      id: `custom-${Date.now()}`,
      title: 'New Section',
      content: 'Add your custom content here...',
      phase: 'Custom',
      editable: true
    };
    setSections(prev => [...prev, newSection]);
    setHasChanges(true);
  };

  const handleDeleteSection = (sectionId: string) => {
    if (sections.length <= 1) {
      toast.error('Cannot delete the last section');
      return;
    }

    setSections(prev => prev.filter(s => s.id !== sectionId));
    setHasChanges(true);
    toast.success('Section deleted successfully!');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-[95vw] max-w-6xl h-[90vh] shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between bg-gradient-to-r from-purple-600 to-blue-600 px-6 py-4 text-white">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center text-2xl">✏️</div>
            <div>
              <h2 className="text-lg font-bold">Edit Roadmap</h2>
              <p className="text-purple-200 text-xs">Customize your roadmap content</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {hasChanges && (
              <span className="text-yellow-200 text-sm">• Unsaved changes</span>
            )}
            <button
              onClick={onClose}
              className="hover:bg-white/10 p-2 rounded-full transition"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
              <p>Loading roadmap editor...</p>
            </div>
          ) : (
            <div className="p-6 space-y-6">
              {/* Add Section Button */}
              <div className="flex justify-end">
                <button
                  onClick={handleAddSection}
                  className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                  <span>+</span>
                  Add Section
                </button>
              </div>

              {/* Sections */}
              {sections.map((section) => (
                <div key={section.id} className="border border-gray-200 rounded-lg overflow-hidden">
                  {/* Section Header */}
                  <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="bg-purple-100 text-purple-800 text-xs font-medium px-2 py-1 rounded-full">
                        {section.phase}
                      </span>
                      <h3 className="font-semibold text-gray-900">{section.title}</h3>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleRegenerateSection(section.id)}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                      >
                        🔄 Regenerate
                      </button>
                      <button
                        onClick={() => handleEditSection(section.id)}
                        className="text-purple-600 hover:text-purple-800 text-sm font-medium"
                      >
                        ✏️ Edit
                      </button>
                      {sections.length > 1 && (
                        <button
                          onClick={() => handleDeleteSection(section.id)}
                          className="text-red-600 hover:text-red-800 text-sm font-medium"
                        >
                          🗑️ Delete
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Section Content */}
                  <div className="p-4">
                    {editingSection === section.id ? (
                      <div className="space-y-4">
                        <textarea
                          value={editContent}
                          onChange={(e) => setEditContent(e.target.value)}
                          className="w-full h-64 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none font-mono text-sm"
                          placeholder="Edit section content..."
                        />
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={handleCancelEdit}
                            className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                          >
                            Cancel
                          </button>
                          <button
                            onClick={handleSaveSection}
                            className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                          >
                            Save Changes
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="prose prose-sm max-w-none">
                        <pre className="whitespace-pre-wrap text-gray-700 font-sans leading-relaxed">
                          {section.content}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Empty State */}
              {sections.length === 0 && (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">📝</div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">No sections found</h3>
                  <p className="text-gray-600 mb-4">Add a section to start editing your roadmap</p>
                  <button
                    onClick={handleAddSection}
                    className="bg-purple-500 hover:bg-purple-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                  >
                    Add First Section
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            {hasChanges ? (
              <span className="text-orange-600">• You have unsaved changes</span>
            ) : (
              <span>All changes saved</span>
            )}
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveRoadmap}
              disabled={isSaving || !hasChanges}
              className="bg-purple-500 hover:bg-purple-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              {isSaving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Saving...
                </>
              ) : (
                <>
                  <span>💾</span>
                  Save Roadmap
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RoadmapEditModal;
