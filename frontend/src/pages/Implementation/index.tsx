import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import ProgressCircle from '../../components/ProgressCircle';
import TaskCard from '../../components/TaskCard';
import TaskCompletionModal from '../../components/TaskCompletionModal';
import ServiceProviderModal from '../../components/ServiceProviderModal';
import KickstartModal from '../../components/KickstartModal';
import HelpModal from '../../components/HelpModal';
import ComprehensiveSupport from '../../components/ComprehensiveSupport';
import { 
  Target, 
  Users, 
  Lightbulb,
  Rocket,
  Phone,
  Settings,
  Megaphone,
  Shield,
  DollarSign
} from 'lucide-react';

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

interface ImplementationProgress {
  completed: number;
  total: number;
  percent: number;
  phases_completed: number;
}

interface ImplementationProps {
  sessionId: string;
  sessionData: any;
  onPhaseChange: (phase: string) => void;
}

const Implementation: React.FC<ImplementationProps> = ({
  sessionId,
  sessionData,
  onPhaseChange
}) => {
  const [currentTask, setCurrentTask] = useState<ImplementationTask | null>(null);
  const [completedTasks, setCompletedTasks] = useState<string[]>([]);
  const [progress, setProgress] = useState<ImplementationProgress>({
    completed: 0,
    total: 25,
    percent: 0,
    phases_completed: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'task' | 'support'>('task');
  
  // Modal states
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [showServiceProviderModal, setShowServiceProviderModal] = useState(false);
  const [showKickstartModal, setShowKickstartModal] = useState(false);
  const [showHelpModal, setShowHelpModal] = useState(false);
  
  // Modal data
  const [serviceProviders, setServiceProviders] = useState<any[]>([]);
  const [kickstartPlan, setKickstartPlan] = useState<any>(null);
  const [helpContent, setHelpContent] = useState<string>('');

  useEffect(() => {
    loadImplementationData();
  }, [sessionId]);

  // Use sessionData for business context if available
  const businessContext = sessionData || {
    business_name: "Your Business",
    industry: "General Business", 
    location: "United States",
    business_type: "Startup"
  };

  const loadImplementationData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/implementation/sessions/${sessionId}/implementation/tasks`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load implementation data');
      }

      const data = await response.json();
      
      if (data.success) {
        setCurrentTask(data.current_task);
        setCompletedTasks(data.completed_tasks || []);
        setProgress(data.progress);
      } else {
        setError(data.message || 'Failed to load implementation data');
      }
    } catch (err) {
      console.error('Error loading implementation data:', err);
      setError('Failed to load implementation data');
    } finally {
      setLoading(false);
    }
  };

  const handleTaskCompletion = async (completionData: any) => {
    if (!currentTask) return;

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/implementation/sessions/${sessionId}/implementation/tasks/${currentTask.id}/complete`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(completionData)
      });

      if (!response.ok) {
        throw new Error('Failed to complete task');
      }

      const data = await response.json();
      
      if (data.success) {
        toast.success('Task completed successfully!');
        setCompletedTasks(prev => [...prev, currentTask.id]);
        setProgress(data.progress);
        
        // Load next task
        await loadImplementationData();
        setShowCompletionModal(false);
      } else {
        toast.error(data.message || 'Failed to complete task');
      }
    } catch (err) {
      console.error('Error completing task:', err);
      toast.error('Failed to complete task');
    }
  };

  const handleGetServiceProviders = async () => {
    if (!currentTask) return;

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/implementation/sessions/${sessionId}/implementation/contact`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ task_id: currentTask.id })
      });

      if (!response.ok) {
        throw new Error('Failed to get service providers');
      }

      const data = await response.json();
      
      if (data.success) {
        setServiceProviders(data.service_providers);
        setShowServiceProviderModal(true);
      } else {
        toast.error(data.message || 'Failed to get service providers');
      }
    } catch (err) {
      console.error('Error getting service providers:', err);
      toast.error('Failed to get service providers');
    }
  };

  const handleGetKickstart = async () => {
    if (!currentTask) return;

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/implementation/sessions/${sessionId}/implementation/tasks/${currentTask.id}/kickstart`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to get kickstart plan');
      }

      const data = await response.json();
      
      if (data.success) {
        setKickstartPlan(data.kickstart_plan);
        setShowKickstartModal(true);
      } else {
        toast.error(data.message || 'Failed to get kickstart plan');
      }
    } catch (err) {
      console.error('Error getting kickstart plan:', err);
      toast.error('Failed to get kickstart plan');
    }
  };

  const handleGetHelp = async () => {
    if (!currentTask) return;

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/implementation/sessions/${sessionId}/implementation/help`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ task_id: currentTask.id, help_type: 'detailed' })
      });

      if (!response.ok) {
        throw new Error('Failed to get help');
      }

      const data = await response.json();
      
      if (data.success) {
        setHelpContent(data.help_content);
        setShowHelpModal(true);
      } else {
        toast.error(data.message || 'Failed to get help');
      }
    } catch (err) {
      console.error('Error getting help:', err);
      toast.error('Failed to get help');
    }
  };

  const handleUploadDocument = async (file: File) => {
    if (!currentTask) return;

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/implementation/sessions/${sessionId}/implementation/tasks/${currentTask.id}/upload-document`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error('Failed to upload document');
      }

      const data = await response.json();
      
      if (data.success) {
        toast.success('Document uploaded successfully!');
      } else {
        toast.error(data.message || 'Failed to upload document');
      }
    } catch (err) {
      console.error('Error uploading document:', err);
      toast.error('Failed to upload document');
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

  const getPhaseName = (phase: string) => {
    switch (phase.toLowerCase()) {
      case 'legal_formation':
        return 'Legal Formation & Compliance';
      case 'financial_setup':
        return 'Financial Planning & Setup';
      case 'operations_development':
        return 'Product & Operations Development';
      case 'marketing_sales':
        return 'Marketing & Sales Strategy';
      case 'launch_scaling':
        return 'Full Launch & Scaling';
      default:
        return phase.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-teal-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading implementation tasks...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-teal-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">❌</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Implementation</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={loadImplementationData}
            className="bg-teal-500 hover:bg-teal-600 text-white px-6 py-2 rounded-lg font-medium transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!currentTask) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-teal-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-green-500 text-6xl mb-4">🎉</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Implementation Complete!</h2>
          <p className="text-gray-600 mb-4">Congratulations! You've completed all implementation tasks.</p>
          <button
            onClick={() => onPhaseChange('COMPLETED')}
            className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-lg font-medium transition-colors"
          >
            View Summary
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-teal-50">
      {/* Header */}
      <div className="bg-white/90 backdrop-blur-xl border-b border-white/30 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Implementation Phase</h1>
              <p className="text-gray-600 mt-1">Turning your roadmap into actionable results</p>
              <div className="flex items-center gap-2 mt-2">
                {getPhaseIcon(currentTask.phase_name)}
                <span className="text-sm font-medium text-gray-700">
                  {getPhaseName(currentTask.phase_name)}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <ProgressCircle
                progress={progress.percent}
                phase="IMPLEMENTATION"
              />
              <div className="text-right">
                <p className="text-sm text-gray-600">Progress</p>
                <p className="text-lg font-semibold text-gray-900">
                  {progress.completed}/{progress.total} tasks
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white/90 backdrop-blur-xl border-b border-white/30">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('task')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'task'
                  ? 'border-teal-500 text-teal-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <Target className="h-4 w-4" />
                Current Task
              </div>
            </button>
            <button
              onClick={() => setActiveTab('support')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'support'
                  ? 'border-teal-500 text-teal-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                Comprehensive Support
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'task' ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Current Task */}
            <div className="lg:col-span-2">
              <TaskCard
                task={currentTask}
                onComplete={() => setShowCompletionModal(true)}
                onGetServiceProviders={handleGetServiceProviders}
                onGetKickstart={handleGetKickstart}
                onGetHelp={handleGetHelp}
                onUploadDocument={handleUploadDocument}
              />
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Progress Overview */}
              <div className="bg-white/90 backdrop-blur-xl border border-white/30 rounded-xl p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Progress Overview</h3>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Tasks Completed</span>
                    <span className="font-medium">{completedTasks.length}/{progress.total}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Phases Completed</span>
                    <span className="font-medium">{progress.phases_completed}/5</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-teal-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${progress.percent}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="bg-white/90 backdrop-blur-xl border border-white/30 rounded-xl p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
                <div className="space-y-3">
                  <button
                    onClick={handleGetHelp}
                    className="w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
                  >
                    <Lightbulb className="h-4 w-4" />
                    Get Help
                  </button>
                  <button
                    onClick={handleGetKickstart}
                    className="w-full bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
                  >
                    <Rocket className="h-4 w-4" />
                    Kickstart Plan
                  </button>
                  <button
                    onClick={handleGetServiceProviders}
                    className="w-full bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
                  >
                    <Phone className="h-4 w-4" />
                    Find Providers
                  </button>
                </div>
              </div>

              {/* Business Context */}
              <div className="bg-white/90 backdrop-blur-xl border border-white/30 rounded-xl p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Business Context</h3>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-gray-600">Business:</span>
                    <span className="font-medium ml-2">{businessContext.business_name || currentTask?.business_context.business_name}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Industry:</span>
                    <span className="font-medium ml-2">{businessContext.industry || currentTask?.business_context.industry}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Location:</span>
                    <span className="font-medium ml-2">{businessContext.location || currentTask?.business_context.location}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <ComprehensiveSupport
            taskContext={currentTask.title}
            businessContext={businessContext}
            onProviderSelect={(provider) => {
              console.log('Provider selected:', provider);
              toast.success('Service provider selected!');
            }}
            onResearchComplete={(result) => {
              console.log('Research completed:', result);
              toast.success('Research completed successfully!');
            }}
            onAgentResponse={(agent, response) => {
              console.log('Agent response:', agent, response);
              toast.success('Agent guidance received!');
            }}
            onCommandComplete={(response) => {
              console.log('Command completed:', response);
              toast.success('Command executed successfully!');
            }}
          />
        )}
      </div>

      {/* Modals */}
      <TaskCompletionModal
        isOpen={showCompletionModal}
        onClose={() => setShowCompletionModal(false)}
        task={currentTask}
        onComplete={handleTaskCompletion}
      />

      <ServiceProviderModal
        isOpen={showServiceProviderModal}
        onClose={() => setShowServiceProviderModal(false)}
        providers={serviceProviders}
        task={currentTask}
      />

      <KickstartModal
        isOpen={showKickstartModal}
        onClose={() => setShowKickstartModal(false)}
        kickstartPlan={kickstartPlan}
        task={currentTask}
      />

      <HelpModal
        isOpen={showHelpModal}
        onClose={() => setShowHelpModal(false)}
        helpContent={helpContent}
        task={currentTask}
      />
    </div>
  );
};

export default Implementation;