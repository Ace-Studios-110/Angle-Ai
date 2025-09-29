import React, { useState } from 'react';
import { 
  Loader2, 
  Building2, 
  Search, 
  Users, 
  Target,
  AlertCircle,
  Settings
} from 'lucide-react';
import ServiceProviderTable from './ServiceProviderTable';
import RAGResearch from './RAGResearch';
import SpecializedAgents from './SpecializedAgents';
import InteractiveCommands from './InteractiveCommands';

interface ComprehensiveSupportProps {
  taskContext?: string;
  businessContext: {
    industry?: string;
    location?: string;
    business_type?: string;
    business_name?: string;
  };
  onProviderSelect?: (provider: any) => void;
  onResearchComplete?: (result: any) => void;
  onAgentResponse?: (agent: any, response: string) => void;
  onCommandComplete?: (response: any) => void;
  className?: string;
}

const ComprehensiveSupport: React.FC<ComprehensiveSupportProps> = ({
  taskContext,
  businessContext,
  onProviderSelect,
  onResearchComplete,
  onAgentResponse,
  onCommandComplete,
  className = ""
}) => {
  const [activeTab, setActiveTab] = useState<string>('providers');
  const [loading] = useState(false);
  const [error] = useState<string | null>(null);

  const tabs = [
    {
      id: 'providers',
      label: 'Service Providers',
      icon: <Building2 className="h-4 w-4" />,
      description: 'Find credible service providers'
    },
    {
      id: 'research',
      label: 'RAG Research',
      icon: <Search className="h-4 w-4" />,
      description: 'Conduct comprehensive research'
    },
    {
      id: 'agents',
      label: 'Specialized Agents',
      icon: <Users className="h-4 w-4" />,
      description: 'Get expert guidance from agents'
    },
    {
      id: 'commands',
      label: 'Interactive Commands',
      icon: <Target className="h-4 w-4" />,
      description: 'Execute interactive commands'
    }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'providers':
        return (
          <ServiceProviderTable
            taskContext={taskContext || 'general business support'}
            businessContext={businessContext}
            onProviderSelect={onProviderSelect}
          />
        );
      case 'research':
        return (
          <RAGResearch
            businessContext={businessContext}
            onResearchComplete={onResearchComplete}
          />
        );
      case 'agents':
        return (
          <SpecializedAgents
            businessContext={businessContext}
            onAgentResponse={onAgentResponse}
          />
        );
      case 'commands':
        return (
          <InteractiveCommands
            businessContext={businessContext}
            onCommandComplete={onCommandComplete}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Settings className="h-5 w-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Comprehensive Support</h2>
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            All-in-One
          </span>
        </div>
        <p className="text-sm text-gray-600 mt-1">
          Access all support tools in one unified interface.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6" aria-label="Tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                {tab.icon}
                <span>{tab.label}</span>
              </div>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500 mx-auto mb-2" />
              <p className="text-gray-600">Loading support tools...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-500" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        )}

        {!loading && !error && (
          <div>
            {/* Tab Description */}
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-2">
                {tabs.find(tab => tab.id === activeTab)?.icon}
                <h3 className="font-medium text-gray-900">
                  {tabs.find(tab => tab.id === activeTab)?.label}
                </h3>
              </div>
              <p className="text-sm text-gray-600">
                {tabs.find(tab => tab.id === activeTab)?.description}
              </p>
            </div>

            {/* Render Active Tab Content */}
            {renderTabContent()}
          </div>
        )}
      </div>

      {/* Business Context Summary */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
        <h3 className="font-semibold text-gray-900 mb-2">Business Context</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Business:</span>
            <span className="font-medium ml-2">{businessContext.business_name || 'Not specified'}</span>
          </div>
          <div>
            <span className="text-gray-600">Industry:</span>
            <span className="font-medium ml-2">{businessContext.industry || 'Not specified'}</span>
          </div>
          <div>
            <span className="text-gray-600">Location:</span>
            <span className="font-medium ml-2">{businessContext.location || 'Not specified'}</span>
          </div>
          <div>
            <span className="text-gray-600">Type:</span>
            <span className="font-medium ml-2">{businessContext.business_type || 'Not specified'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComprehensiveSupport;