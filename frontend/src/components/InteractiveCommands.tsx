import React, { useState } from 'react';
import { toast } from 'react-toastify';
import { 
  Loader2, 
  HelpCircle, 
  Phone, 
  Edit3, 
  FileText, 
  Rocket,
  AlertCircle,
  CheckCircle,
  Building2
} from 'lucide-react';
import httpClient from '../api/httpClient';

interface CommandResponse {
  command: string;
  type: string;
  guidance?: any;
  providers?: any;
  refined_insights?: string;
  draft_content?: any;
  kickstart_plan?: any;
  provider_table?: any;
  message?: string;
}

interface InteractiveCommandsProps {
  businessContext: {
    industry?: string;
    location?: string;
    business_type?: string;
    business_name?: string;
  };
  onCommandComplete?: (response: CommandResponse) => void;
  className?: string;
}

const InteractiveCommands: React.FC<InteractiveCommandsProps> = ({
  businessContext,
  onCommandComplete,
  className = ""
}) => {
  const [selectedCommand, setSelectedCommand] = useState<string>('');
  const [context, setContext] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<CommandResponse | null>(null);

  const commands = [
    {
      id: 'help',
      name: 'Help',
      description: 'Get detailed assistance and guidance',
      icon: <HelpCircle className="h-5 w-5" />,
      color: 'bg-blue-500 hover:bg-blue-600'
    },
    {
      id: 'contact',
      name: 'Who do I contact?',
      description: 'Find service providers and contacts',
      icon: <Phone className="h-5 w-5" />,
      color: 'bg-green-500 hover:bg-green-600'
    },
    {
      id: 'scrapping',
      name: 'Scrapping',
      description: 'Research and analyze information',
      icon: <Edit3 className="h-5 w-5" />,
      color: 'bg-purple-500 hover:bg-purple-600'
    },
    {
      id: 'draft',
      name: 'Draft',
      description: 'Create documents and templates',
      icon: <FileText className="h-5 w-5" />,
      color: 'bg-orange-500 hover:bg-orange-600'
    },
    {
      id: 'kickstart',
      name: 'Kickstart',
      description: 'Get detailed action plan',
      icon: <Rocket className="h-5 w-5" />,
      color: 'bg-red-500 hover:bg-red-600'
    }
  ];

  const executeCommand = async () => {
    if (!selectedCommand || !context.trim()) {
      setError('Please select a command and provide context');
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

      const response = await httpClient.post('/specialized-agents/interactive-command', {
        command: selectedCommand,
        context: context.trim(),
        business_context: businessContext
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if ((response.data as any).success) {
        const commandResponse: CommandResponse = {
          command: selectedCommand,
          type: (response.data as any).result.type,
          ...(response.data as any).result
        };
        
        setResponse(commandResponse);
        onCommandComplete?.(commandResponse);
        toast.success(`Command "${selectedCommand}" executed successfully!`);
      } else {
        setError((response.data as any).message || 'Failed to execute command');
      }
    } catch (err: any) {
      console.error('Error executing command:', err);
      setError(err.response?.data?.message || 'Failed to execute command');
    } finally {
      setLoading(false);
    }
  };

  const getResponseIcon = (type: string) => {
    switch (type) {
      case 'help':
        return <HelpCircle className="h-5 w-5 text-blue-500" />;
      case 'contact':
        return <Phone className="h-5 w-5 text-green-500" />;
      case 'scrapping':
        return <Edit3 className="h-5 w-5 text-purple-500" />;
      case 'draft':
        return <FileText className="h-5 w-5 text-orange-500" />;
      case 'kickstart':
        return <Rocket className="h-5 w-5 text-red-500" />;
      default:
        return <CheckCircle className="h-5 w-5 text-gray-500" />;
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Building2 className="h-5 w-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Interactive Commands</h2>
        </div>
        <p className="text-sm text-gray-600 mt-1">
          Use these commands to get specific assistance with your business development tasks.
        </p>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Command Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">Select Command</label>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {commands.map((cmd) => (
              <button
                key={cmd.id}
                onClick={() => setSelectedCommand(cmd.id)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  selectedCommand === cmd.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${cmd.color} text-white`}>
                    {cmd.icon}
                  </div>
                  <div className="text-left">
                    <div className="font-medium text-gray-900">{cmd.name}</div>
                    <div className="text-xs text-gray-600">{cmd.description}</div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Context Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Provide Context for "{selectedCommand || 'selected command'}"
          </label>
          <textarea
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="Describe what you need help with or what you want to accomplish..."
            rows={4}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Execute Button */}
        <div className="flex justify-end">
          <button
            onClick={executeCommand}
            disabled={loading || !selectedCommand || !context.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Executing...
              </>
            ) : (
              <>
                <Rocket className="h-4 w-4" />
                Execute Command
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

        {/* Response Display */}
        {response && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              {getResponseIcon(response.type)}
              <h3 className="font-medium text-gray-900">
                {response.command.charAt(0).toUpperCase() + response.command.slice(1)} Response
              </h3>
            </div>
            
            <div className="space-y-3">
              {response.guidance && (
                <div>
                  <h4 className="font-medium text-gray-800 mb-2">Guidance</h4>
                  <div className="bg-white p-3 rounded border">
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">{response.guidance}</p>
                  </div>
                </div>
              )}
              
              {response.providers && (
                <div>
                  <h4 className="font-medium text-gray-800 mb-2">Service Providers</h4>
                  <div className="bg-white p-3 rounded border">
                    <p className="text-sm text-gray-700">{JSON.stringify(response.providers, null, 2)}</p>
                  </div>
                </div>
              )}
              
              {response.draft_content && (
                <div>
                  <h4 className="font-medium text-gray-800 mb-2">Draft Content</h4>
                  <div className="bg-white p-3 rounded border">
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">{response.draft_content}</p>
                  </div>
                </div>
              )}
              
              {response.kickstart_plan && (
                <div>
                  <h4 className="font-medium text-gray-800 mb-2">Kickstart Plan</h4>
                  <div className="bg-white p-3 rounded border">
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">{response.kickstart_plan}</p>
                  </div>
                </div>
              )}
              
              {response.message && (
                <div>
                  <h4 className="font-medium text-gray-800 mb-2">Message</h4>
                  <div className="bg-white p-3 rounded border">
                    <p className="text-sm text-gray-700">{response.message}</p>
                  </div>
                </div>
              )}
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

export default InteractiveCommands;