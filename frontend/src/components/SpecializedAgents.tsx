import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { 
  Loader2, 
  Users, 
  Lightbulb, 
  AlertCircle, 
  CheckCircle,
  Building2,
  Shield,
  DollarSign,
  Settings,
  Megaphone,
  Target,
  Rocket,
  FileText
} from 'lucide-react';
import httpClient from '../api/httpClient';

interface Agent {
  name: string;
  expertise: string;
  research_sources: string[];
  guidance: string;
  agent_type: string;
}

interface SpecializedAgentsProps {
  businessContext: {
    industry?: string;
    location?: string;
    business_type?: string;
    business_name?: string;
  };
  onAgentResponse?: (agent: Agent, response: string) => void;
  className?: string;
}

const SpecializedAgents: React.FC<SpecializedAgentsProps> = ({
  businessContext,
  onAgentResponse,
  className = ""
}) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [question, setQuestion] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<string>('');

  useEffect(() => {
    fetchAvailableAgents();
  }, []);

  const fetchAvailableAgents = async () => {
    try {
      const token = localStorage.getItem('sb_access_token');
      if (!token) return;

      const response = await httpClient.get('/specialized-agents/agents', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if ((response.data as any).success) {
        setAgents((response.data as any).agents);
      } else {
        setError((response.data as any).message || 'Failed to fetch agents');
      }
    } catch (err: any) {
      console.error('Error fetching agents:', err);
      setError(err.response?.data?.message || 'Failed to fetch agents');
    }
  };

  const getAgentGuidance = async () => {
    if (!selectedAgent || !question.trim()) {
      setError('Please select an agent and enter a question');
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('sb_access_token');
      if (!token) {
        setError('Authentication required');
        return;
      }

      const response = await httpClient.post('/specialized-agents/agent-guidance', {
        question: question.trim(),
        agent_type: selectedAgent,
        business_context: businessContext
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if ((response.data as any).success) {
        const guidance = (response.data as any).result.guidance || 'No guidance available';
        setResponse(guidance);
        
        const agent = agents.find(a => a.agent_type === selectedAgent);
        if (agent) {
          onAgentResponse?.(agent, guidance);
        }
        
        toast.success('Agent guidance received successfully!');
      } else {
        setError((response.data as any).message || 'Failed to get agent guidance');
      }
    } catch (err: any) {
      console.error('Error getting agent guidance:', err);
      setError(err.response?.data?.message || 'Failed to get agent guidance');
    } finally {
      setLoading(false);
    }
  };

  const getAgentIcon = (agentType: string) => {
    switch (agentType) {
      case 'legal_compliance':
        return <Shield className="h-5 w-5 text-blue-500" />;
      case 'financial_planning':
        return <DollarSign className="h-5 w-5 text-green-500" />;
      case 'product_operations':
        return <Settings className="h-5 w-5 text-purple-500" />;
      case 'marketing_customer':
        return <Megaphone className="h-5 w-5 text-orange-500" />;
      case 'business_strategy':
        return <Target className="h-5 w-5 text-red-500" />;
      case 'roadmap_execution':
        return <Rocket className="h-5 w-5 text-indigo-500" />;
      default:
        return <Users className="h-5 w-5 text-gray-500" />;
    }
  };

  const getAgentColor = (agentType: string) => {
    switch (agentType) {
      case 'legal_compliance':
        return 'bg-blue-100 text-blue-800';
      case 'financial_planning':
        return 'bg-green-100 text-green-800';
      case 'product_operations':
        return 'bg-purple-100 text-purple-800';
      case 'marketing_customer':
        return 'bg-orange-100 text-orange-800';
      case 'business_strategy':
        return 'bg-red-100 text-red-800';
      case 'roadmap_execution':
        return 'bg-indigo-100 text-indigo-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Specialized Agents</h2>
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
            Expert Guidance
          </span>
        </div>
        <p className="text-sm text-gray-600 mt-1">
          Get expert guidance from specialized agents trained on credible sources.
        </p>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Agent Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">Select Specialized Agent</label>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {agents.map((agent) => (
              <button
                key={agent.agent_type}
                onClick={() => setSelectedAgent(agent.agent_type)}
                className={`p-4 rounded-lg border-2 text-left transition-all ${
                  selectedAgent === agent.agent_type
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  {getAgentIcon(agent.agent_type)}
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{agent.name}</div>
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getAgentColor(agent.agent_type)}`}>
                      {agent.agent_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-600">{agent.expertise}</p>
                <div className="mt-2">
                  <div className="text-xs font-medium text-gray-500 mb-1">Research Sources:</div>
                  <div className="flex flex-wrap gap-1">
                    {agent.research_sources.slice(0, 2).map((source, index) => (
                      <span key={index} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                        {source}
                      </span>
                    ))}
                    {agent.research_sources.length > 2 && (
                      <span className="text-xs text-gray-500">
                        +{agent.research_sources.length - 2} more
                      </span>
                    )}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Question Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Ask {selectedAgent ? agents.find(a => a.agent_type === selectedAgent)?.name : 'an agent'}
          </label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Enter your question or request for guidance..."
            rows={4}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Get Guidance Button */}
        <div className="flex justify-end">
          <button
            onClick={getAgentGuidance}
            disabled={loading || !selectedAgent || !question.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Getting Guidance...
              </>
            ) : (
              <>
                <Lightbulb className="h-4 w-4" />
                Get Expert Guidance
              </>
            )}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-500" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        )}

        {/* Agent Response */}
        {response && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <h3 className="font-medium text-gray-900">
                {agents.find(a => a.agent_type === selectedAgent)?.name} Response
              </h3>
            </div>
            <div className="bg-white p-4 rounded border">
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{response}</p>
            </div>
          </div>
        )}

        {/* Business Context */}
        <div className="pt-4 border-t border-gray-200">
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
    </div>
  );
};

export default SpecializedAgents;