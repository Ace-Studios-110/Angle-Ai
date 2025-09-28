import React, { useState, useEffect } from 'react';
import { 
  Loader2, 
  CheckCircle, 
  Clock, 
  AlertTriangle, 
  Lightbulb, 
  Rocket, 
  Phone, 
  FileText,
  Target,
  Building2,
  TrendingUp,
  Shield,
  DollarSign,
  Settings,
  Megaphone
} from 'lucide-react';
import httpClient from '../api/httpClient';

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

interface TaskCardProps {
  task: ImplementationTask;
  onComplete: () => void;
  onGetServiceProviders: () => void;
  onGetKickstart: () => void;
  onGetHelp: () => void;
  onUploadDocument: (file: File) => void;
}

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onComplete,
  onGetServiceProviders,
  onGetKickstart,
  onGetHelp,
  onUploadDocument
}) => {
  const [selectedOption, setSelectedOption] = useState<string>('');
  const [completionNotes, setCompletionNotes] = useState<string>('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mentorInsights, setMentorInsights] = useState<string>('');
  const [ragResearch, setRagResearch] = useState<any>(null);

  useEffect(() => {
    loadTaskInsights();
  }, [task.id]);

  const loadTaskInsights = async () => {
    try {
      const token = localStorage.getItem('sb_access_token');
      if (!token) return;

      // Load mentor insights and RAG research for this task
      const response = await httpClient.post('/specialized-agents/agent-guidance', {
        question: `Provide expert guidance for implementation task: ${task.title}`,
        agent_type: 'comprehensive',
        business_context: task.business_context
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if ((response.data as any).success) {
        setMentorInsights((response.data as any).result.guidance || 'Expert guidance will be provided as you work through this task.');
      }

      // Load RAG research
      const ragResponse = await httpClient.post('/specialized-agents/rag-research', {
        query: `implementation task ${task.id} ${task.business_context.industry} ${task.business_context.location}`,
        business_context: task.business_context,
        research_depth: 'standard'
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if ((ragResponse.data as any).success) {
        setRagResearch((ragResponse.data as any).result);
      }
    } catch (err) {
      console.error('Error loading task insights:', err);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      onUploadDocument(file);
    }
  };

  const handleComplete = async () => {
    if (!selectedOption && task.options.length > 0) {
      setError('Please select an option before completing the task');
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

      const completionData = {
        selected_option: selectedOption,
        completion_notes: completionNotes,
        uploaded_file: uploadedFile?.name,
        completed_at: new Date().toISOString()
      };

      const response = await httpClient.post(`/implementation/sessions/${task.id}/implementation/tasks/${task.id}/complete`, completionData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if ((response.data as any).success) {
        onComplete();
      } else {
        setError((response.data as any).message || 'Failed to complete task');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to complete task');
    } finally {
      setLoading(false);
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'medium':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      default:
        return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-green-100 text-green-800';
    }
  };

  const getPhaseIcon = (phase: string) => {
    switch (phase.toLowerCase()) {
      case 'legal_formation':
        return <Shield className="h-5 w-5 text-blue-600" />;
      case 'financial_setup':
        return <DollarSign className="h-5 w-5 text-green-600" />;
      case 'operations_development':
        return <Settings className="h-5 w-5 text-purple-600" />;
      case 'marketing_sales':
        return <Megaphone className="h-5 w-5 text-orange-600" />;
      case 'launch_scaling':
        return <Rocket className="h-5 w-5 text-red-600" />;
      default:
        return <Target className="h-5 w-5 text-gray-600" />;
    }
  };

  return (
    <div className="w-full bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            {getPhaseIcon(task.phase_name)}
            <div>
              <h2 className="text-xl font-semibold text-gray-900">{task.title}</h2>
              <div className="flex items-center gap-2 mt-1">
                <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(task.priority)}`}>
                  {getPriorityIcon(task.priority)}
                  {task.priority} Priority
                </span>
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                  <Clock className="h-3 w-3" />
                  {task.estimated_time}
                </span>
              </div>
            </div>
          </div>
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 capitalize">
            {task.phase_name.replace('_', ' ')}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Task Description */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Task Description</h3>
          <p className="text-gray-700">{task.description}</p>
        </div>

        {/* Purpose */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">Purpose</h3>
          <p className="text-gray-700">{task.purpose}</p>
        </div>

        {/* Decision Options */}
        {task.options.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Select Your Option</label>
            <select 
              value={selectedOption} 
              onChange={(e) => setSelectedOption(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Choose an option...</option>
              {task.options.map((option, index) => (
                <option key={index} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Angel Actions */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Building2 className="h-4 w-4 text-blue-600" />
            Angel Can Help You With
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {task.angel_actions.map((action, index) => (
              <div key={index} className="flex items-center gap-2 p-2 bg-blue-50 rounded-lg">
                <CheckCircle className="h-4 w-4 text-blue-600" />
                <span className="text-sm text-blue-800">{action}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Mentor Insights */}
        {mentorInsights && (
          <div>
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-yellow-600" />
              Mentor Insights
            </h3>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <p className="text-sm text-yellow-800 whitespace-pre-wrap">{mentorInsights}</p>
            </div>
          </div>
        )}

        {/* RAG Research */}
        {ragResearch && (
          <div>
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-600" />
              Research-Backed Guidance
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                RAG-Powered
              </span>
            </h3>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-sm text-green-800 mb-2">
                Sources consulted: {ragResearch.sources_consulted} authoritative sources
              </p>
              <p className="text-sm text-green-800 whitespace-pre-wrap">
                {ragResearch.analysis}
              </p>
            </div>
          </div>
        )}

        {/* Completion Notes */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Completion Notes</label>
          <textarea
            placeholder="Describe what you accomplished, decisions made, or any important details..."
            value={completionNotes}
            onChange={(e) => setCompletionNotes(e.target.value)}
            rows={3}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Document Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Upload Documentation</label>
          <div className="mt-2">
            <input
              type="file"
              accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
              onChange={handleFileUpload}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            {uploadedFile && (
              <div className="mt-2 flex items-center gap-2 text-sm text-green-600">
                <FileText className="h-4 w-4" />
                {uploadedFile.name}
              </div>
            )}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={handleComplete}
            disabled={loading || (task.options.length > 0 && !selectedOption)}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Completing Task...
              </>
            ) : (
              <>
                <CheckCircle className="h-4 w-4" />
                Complete Task
              </>
            )}
          </button>

          <div className="flex gap-2">
            <button
              onClick={onGetHelp}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Lightbulb className="h-4 w-4" />
              Help
            </button>

            <button
              onClick={onGetKickstart}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Rocket className="h-4 w-4" />
              Kickstart
            </button>

            <button
              onClick={onGetServiceProviders}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Phone className="h-4 w-4" />
              Contact
            </button>
          </div>
        </div>

        {/* Business Context */}
        <div className="pt-4 border-t border-gray-200">
          <h3 className="font-semibold text-gray-900 mb-2">Business Context</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Business:</span>
              <span className="font-medium ml-2">{task.business_context.business_name}</span>
            </div>
            <div>
              <span className="text-gray-600">Industry:</span>
              <span className="font-medium ml-2">{task.business_context.industry}</span>
            </div>
            <div>
              <span className="text-gray-600">Location:</span>
              <span className="font-medium ml-2">{task.business_context.location}</span>
            </div>
            <div>
              <span className="text-gray-600">Type:</span>
              <span className="font-medium ml-2">{task.business_context.business_type}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskCard;