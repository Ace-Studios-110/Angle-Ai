import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Alert, AlertDescription } from './ui/alert';
import { 
  CheckCircle, 
  Circle, 
  AlertTriangle, 
  Info, 
  Lightbulb, 
  Users, 
  Phone, 
  FileText, 
  Rocket, 
  HelpCircle,
  Navigation,
  X,
  ChevronRight,
  ChevronDown,
  Target,
  TrendingUp,
  Clock,
} from 'lucide-react';

// Types
interface ProgressIndicator {
  id: string;
  label: string;
  progress: number;
  type: 'overall' | 'section' | 'task';
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  phase?: string;
  section?: string;
}

interface DynamicPrompt {
  id: string;
  type: 'notification' | 'reminder' | 'suggestion' | 'warning' | 'success';
  title: string;
  message: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  dismissible: boolean;
  priority: 'low' | 'medium' | 'high' | 'critical';
  expires_at?: Date;
}

interface InteractiveCommand {
  command: string;
  description: string;
  icon: React.ReactNode;
  action: () => void;
  available: boolean;
}

interface NavigationItem {
  id: string;
  label: string;
  phase: string;
  status: 'completed' | 'current' | 'upcoming' | 'locked';
  icon: React.ReactNode;
  description?: string;
  tasks?: NavigationItem[];
}

interface CompletionDeclaration {
  task_id: string;
  summary: string;
  decisions: string[];
  actions_taken: string[];
  documents_uploaded: string[];
  completion_date: Date;
  next_steps: string[];
}

// Progress Indicators Component
export const ProgressIndicators: React.FC<{
  indicators: ProgressIndicator[];
  showDetails?: boolean;
}> = ({ indicators, showDetails = false }) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'in_progress':
        return <Clock className="h-4 w-4 text-blue-500" />;
      case 'blocked':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default:
        return <Circle className="h-4 w-4 text-gray-400" />;
    }
  };

  // const getStatusColor = (status: string) => {
  //   switch (status) {
  //     case 'completed':
  //       return 'bg-green-500';
  //     case 'in_progress':
  //       return 'bg-blue-500';
  //     case 'blocked':
  //       return 'bg-red-500';
  //     default:
  //       return 'bg-gray-300';
  //   }
  // };

  return (
    <div className="space-y-4">
      {indicators.map((indicator) => (
        <Card key={indicator.id} className="w-full">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {getStatusIcon(indicator.status)}
                <CardTitle className="text-sm font-medium">{indicator.label}</CardTitle>
                <Badge variant="outline" className="text-xs">
                  {indicator.type}
                </Badge>
              </div>
              <span className="text-sm text-gray-600">{indicator.progress}%</span>
            </div>
          </CardHeader>
          <CardContent>
            <Progress value={indicator.progress} className="w-full" />
            {showDetails && (
              <div className="mt-2 text-xs text-gray-600">
                {indicator.phase && <span>Phase: {indicator.phase}</span>}
                {indicator.section && <span className="ml-2">Section: {indicator.section}</span>}
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

// Dynamic Prompts Component
export const DynamicPrompts: React.FC<{
  prompts: DynamicPrompt[];
  onDismiss: (promptId: string) => void;
}> = ({ prompts, onDismiss }) => {
  const getPromptIcon = (type: string) => {
    switch (type) {
      case 'notification':
        return <Info className="h-4 w-4 text-blue-500" />;
      case 'reminder':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'suggestion':
        return <Lightbulb className="h-4 w-4 text-purple-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-orange-500" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      default:
        return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  const getPromptColor = (type: string) => {
    switch (type) {
      case 'notification':
        return 'border-blue-200 bg-blue-50';
      case 'reminder':
        return 'border-yellow-200 bg-yellow-50';
      case 'suggestion':
        return 'border-purple-200 bg-purple-50';
      case 'warning':
        return 'border-orange-200 bg-orange-50';
      case 'success':
        return 'border-green-200 bg-green-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  return (
    <div className="space-y-3">
      {prompts.map((prompt) => (
        <Alert key={prompt.id} className={getPromptColor(prompt.type)}>
          <div className="flex items-start gap-2">
            {getPromptIcon(prompt.type)}
            <div className="flex-1">
              <AlertDescription>
                <div className="font-medium">{prompt.title}</div>
                <div className="text-sm mt-1">{prompt.message}</div>
                {prompt.action && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={prompt.action.onClick}
                    className="mt-2"
                  >
                    {prompt.action.label}
                  </Button>
                )}
              </AlertDescription>
            </div>
            {prompt.dismissible && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => onDismiss(prompt.id)}
                className="p-1 h-auto"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </Alert>
      ))}
    </div>
  );
};

// Interactive Commands Component
export const InteractiveCommands: React.FC<{
  commands: InteractiveCommand[];
  onCommandExecute: (command: string) => void;
}> = ({ commands, onCommandExecute }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
      {commands.map((cmd) => (
        <Button
          key={cmd.command}
          variant="outline"
          onClick={() => {
            cmd.action();
            onCommandExecute(cmd.command);
          }}
          disabled={!cmd.available}
          className="h-auto p-4 flex flex-col items-center gap-2"
        >
          {cmd.icon}
          <div className="text-center">
            <div className="font-medium">{cmd.command}</div>
            <div className="text-xs text-gray-600">{cmd.description}</div>
          </div>
        </Button>
      ))}
    </div>
  );
};

// Flexible Navigation Component
export const FlexibleNavigation: React.FC<{
  items: NavigationItem[];
  currentPhase: string;
  onNavigate: (item: NavigationItem) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}> = ({ items, onNavigate, collapsed = false, onToggleCollapse }) => {
  const [expandedItems, setExpandedItems] = useState<string[]>([]);

  const toggleExpanded = (itemId: string) => {
    setExpandedItems(prev =>
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'current':
        return <Target className="h-4 w-4 text-blue-500" />;
      case 'upcoming':
        return <Clock className="h-4 w-4 text-gray-400" />;
      case 'locked':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default:
        return <Circle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50';
      case 'current':
        return 'text-blue-600 bg-blue-50';
      case 'upcoming':
        return 'text-gray-600 bg-gray-50';
      case 'locked':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const renderNavigationItem = (item: NavigationItem, level: number = 0) => (
    <div key={item.id} className={`${level > 0 ? 'ml-4' : ''}`}>
      <div
        className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-colors ${
          item.status === 'locked' ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-100'
        } ${getStatusColor(item.status)}`}
        onClick={() => {
          if (item.status !== 'locked') {
            onNavigate(item);
          }
        }}
      >
        {getStatusIcon(item.status)}
        {item.icon}
        <span className="flex-1 text-sm font-medium">{item.label}</span>
        {item.tasks && item.tasks.length > 0 && (
          <Button
            size="sm"
            variant="ghost"
            onClick={(e: React.MouseEvent) => {
              e.stopPropagation();
              toggleExpanded(item.id);
            }}
            className="p-1 h-auto"
          >
            {expandedItems.includes(item.id) ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </Button>
        )}
      </div>
      {item.description && (
        <div className="text-xs text-gray-600 ml-6 mb-2">{item.description}</div>
      )}
      {item.tasks && expandedItems.includes(item.id) && (
        <div className="ml-4 space-y-1">
          {item.tasks.map((task) => renderNavigationItem(task, level + 1))}
        </div>
      )}
    </div>
  );

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Navigation className="h-5 w-5" />
            Navigation
          </CardTitle>
          {onToggleCollapse && (
            <Button
              size="sm"
              variant="ghost"
              onClick={onToggleCollapse}
              className="p-1 h-auto"
            >
              {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
          )}
        </div>
      </CardHeader>
      {!collapsed && (
        <CardContent>
          <div className="space-y-1">
            {items.map((item) => renderNavigationItem(item))}
          </div>
        </CardContent>
      )}
    </Card>
  );
};

// Completion Declaration Component
export const CompletionDeclaration: React.FC<{
  taskId: string;
  taskTitle: string;
  onComplete: (declaration: CompletionDeclaration) => void;
  onCancel: () => void;
}> = ({ taskId, taskTitle, onComplete, onCancel }) => {
  const [summary, setSummary] = useState('');
  const [decisions, setDecisions] = useState<string[]>(['']);
  const [actionsTaken, setActionsTaken] = useState<string[]>(['']);
  const [documentsUploaded, setDocumentsUploaded] = useState<string[]>([]);
  const [nextSteps, setNextSteps] = useState<string[]>(['']);

  const addDecision = () => setDecisions([...decisions, '']);
  const removeDecision = (index: number) => setDecisions(decisions.filter((_, i) => i !== index));
  const updateDecision = (index: number, value: string) => {
    const updated = [...decisions];
    updated[index] = value;
    setDecisions(updated);
  };

  const addAction = () => setActionsTaken([...actionsTaken, '']);
  const removeAction = (index: number) => setActionsTaken(actionsTaken.filter((_, i) => i !== index));
  const updateAction = (index: number, value: string) => {
    const updated = [...actionsTaken];
    updated[index] = value;
    setActionsTaken(updated);
  };

  const addNextStep = () => setNextSteps([...nextSteps, '']);
  const removeNextStep = (index: number) => setNextSteps(nextSteps.filter((_, i) => i !== index));
  const updateNextStep = (index: number, value: string) => {
    const updated = [...nextSteps];
    updated[index] = value;
    setNextSteps(updated);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      const fileNames = Array.from(files).map(file => file.name);
      setDocumentsUploaded([...documentsUploaded, ...fileNames]);
    }
  };

  const handleComplete = () => {
    const declaration: CompletionDeclaration = {
      task_id: taskId,
      summary,
      decisions: decisions.filter(d => d.trim() !== ''),
      actions_taken: actionsTaken.filter(a => a.trim() !== ''),
      documents_uploaded: documentsUploaded,
      completion_date: new Date(),
      next_steps: nextSteps.filter(s => s.trim() !== '')
    };
    onComplete(declaration);
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle className="h-5 w-5 text-green-500" />
          Complete Task: {taskTitle}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary */}
        <div>
          <label className="block text-sm font-medium mb-2">Task Summary</label>
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="Summarize what you accomplished in this task..."
            className="w-full p-3 border rounded-lg"
            rows={3}
          />
        </div>

        {/* Decisions Made */}
        <div>
          <label className="block text-sm font-medium mb-2">Decisions Made</label>
          {decisions.map((decision, index) => (
            <div key={index} className="flex gap-2 mb-2">
              <input
                type="text"
                value={decision}
                onChange={(e) => updateDecision(index, e.target.value)}
                placeholder="Describe a decision you made..."
                className="flex-1 p-2 border rounded"
              />
              <Button
                size="sm"
                variant="outline"
                onClick={() => removeDecision(index)}
                disabled={decisions.length === 1}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button size="sm" variant="outline" onClick={addDecision}>
            Add Decision
          </Button>
        </div>

        {/* Actions Taken */}
        <div>
          <label className="block text-sm font-medium mb-2">Actions Taken</label>
          {actionsTaken.map((action, index) => (
            <div key={index} className="flex gap-2 mb-2">
              <input
                type="text"
                value={action}
                onChange={(e) => updateAction(index, e.target.value)}
                placeholder="Describe an action you took..."
                className="flex-1 p-2 border rounded"
              />
              <Button
                size="sm"
                variant="outline"
                onClick={() => removeAction(index)}
                disabled={actionsTaken.length === 1}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button size="sm" variant="outline" onClick={addAction}>
            Add Action
          </Button>
        </div>

        {/* Document Upload */}
        <div>
          <label className="block text-sm font-medium mb-2">Upload Documentation</label>
          <input
            type="file"
            multiple
            onChange={handleFileUpload}
            className="w-full p-2 border rounded"
            accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
          />
          {documentsUploaded.length > 0 && (
            <div className="mt-2">
              <div className="text-sm font-medium">Uploaded Files:</div>
              <ul className="text-sm text-gray-600">
                {documentsUploaded.map((file, index) => (
                  <li key={index}>• {file}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Next Steps */}
        <div>
          <label className="block text-sm font-medium mb-2">Next Steps</label>
          {nextSteps.map((step, index) => (
            <div key={index} className="flex gap-2 mb-2">
              <input
                type="text"
                value={step}
                onChange={(e) => updateNextStep(index, e.target.value)}
                placeholder="What's your next step?"
                className="flex-1 p-2 border rounded"
              />
              <Button
                size="sm"
                variant="outline"
                onClick={() => removeNextStep(index)}
                disabled={nextSteps.length === 1}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button size="sm" variant="outline" onClick={addNextStep}>
            Add Next Step
          </Button>
        </div>

        {/* Actions */}
        <div className="flex gap-3 justify-end">
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button onClick={handleComplete} disabled={!summary.trim()}>
            Complete Task
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

// Main UX Guidelines Manager Component
export const UXGuidelinesManager: React.FC<{
  currentPhase: string;
  progressData: ProgressIndicator[];
  onPhaseChange: (phase: string) => void;
  onCommandExecute: (command: string) => void;
}> = ({ currentPhase, progressData, onPhaseChange, onCommandExecute }) => {
  const [prompts, setPrompts] = useState<DynamicPrompt[]>([]);
  const [navigationCollapsed, setNavigationCollapsed] = useState(false);
  const [showCompletionModal, setShowCompletionModal] = useState(false);

  // Interactive commands
  const interactiveCommands: InteractiveCommand[] = [
    {
      command: "Help",
      description: "Get detailed assistance",
      icon: <HelpCircle className="h-5 w-5" />,
      action: () => onCommandExecute("help"),
      available: true
    },
    {
      command: "Who do I contact?",
      description: "Find service providers",
      icon: <Phone className="h-5 w-5" />,
      action: () => onCommandExecute("contact"),
      available: true
    },
    {
      command: "Scrapping",
      description: "Research and analyze",
      icon: <TrendingUp className="h-5 w-5" />,
      action: () => onCommandExecute("scrapping"),
      available: true
    },
    {
      command: "Draft",
      description: "Create documents",
      icon: <FileText className="h-5 w-5" />,
      action: () => onCommandExecute("draft"),
      available: true
    },
    {
      command: "Kickstart",
      description: "Get action plan",
      icon: <Rocket className="h-5 w-5" />,
      action: () => onCommandExecute("kickstart"),
      available: true
    }
  ];

  // Navigation items
  const navigationItems: NavigationItem[] = [
    {
      id: "kyc",
      label: "KYC Intake Questionnaire",
      phase: "KYC",
      status: "completed",
      icon: <Users className="h-4 w-4" />,
      description: "Initial business information gathering"
    },
    {
      id: "business_plan",
      label: "Business Plan Development",
      phase: "PLANNING",
      status: "completed",
      icon: <FileText className="h-4 w-4" />,
      description: "Comprehensive business planning"
    },
    {
      id: "roadmap",
      label: "Launch Roadmap",
      phase: "ROADMAPPING",
      status: "current",
      icon: <Target className="h-4 w-4" />,
      description: "Step-by-step implementation plan"
    },
    {
      id: "implementation",
      label: "Implementation Phase",
      phase: "IMPLEMENTATION",
      status: "upcoming",
      icon: <Rocket className="h-4 w-4" />,
      description: "Execute your business plan"
    }
  ];

  // Generate dynamic prompts based on current state
  useEffect(() => {
    const newPrompts: DynamicPrompt[] = [];
    
    // Progress-based prompts
    const currentProgress = progressData.find(p => p.type === 'overall');
    if (currentProgress && currentProgress.progress > 0) {
      newPrompts.push({
        id: "progress_update",
        type: "success",
        title: "Great Progress!",
        message: `You've completed ${currentProgress.progress}% of your journey. Keep up the excellent work!`,
        dismissible: true,
        priority: "medium"
      });
    }

    // Phase-specific prompts
    if (currentPhase === "IMPLEMENTATION") {
      newPrompts.push({
        id: "implementation_tip",
        type: "suggestion",
        title: "Implementation Tip",
        message: "Remember to declare task completions and upload relevant documentation to keep your progress updated.",
        action: {
          label: "Learn More",
          onClick: () => setShowCompletionModal(true)
        },
        dismissible: true,
        priority: "high"
      });
    }

    setPrompts(newPrompts);
  }, [currentPhase, progressData]);

  const dismissPrompt = (promptId: string) => {
    setPrompts(prev => prev.filter(p => p.id !== promptId));
  };

  const handleNavigation = (item: NavigationItem) => {
    onPhaseChange(item.phase);
  };

  const handleCompletionDeclaration = (declaration: CompletionDeclaration) => {
    console.log('Task completed:', declaration);
    setShowCompletionModal(false);
    // Here you would typically send the declaration to your backend
  };

  return (
    <div className="space-y-6">
      {/* Progress Indicators */}
      <ProgressIndicators indicators={progressData} showDetails={true} />
      
      {/* Dynamic Prompts */}
      {prompts.length > 0 && (
        <DynamicPrompts prompts={prompts} onDismiss={dismissPrompt} />
      )}
      
      {/* Interactive Commands */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Interactive Commands</CardTitle>
        </CardHeader>
        <CardContent>
          <InteractiveCommands 
            commands={interactiveCommands} 
            onCommandExecute={onCommandExecute}
          />
        </CardContent>
      </Card>
      
      {/* Flexible Navigation */}
      <FlexibleNavigation
        items={navigationItems}
        currentPhase={currentPhase}
        onNavigate={handleNavigation}
        collapsed={navigationCollapsed}
        onToggleCollapse={() => setNavigationCollapsed(!navigationCollapsed)}
      />
      
      {/* Completion Declaration Modal */}
      {showCompletionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <CompletionDeclaration
            taskId="current_task"
            taskTitle="Current Task"
            onComplete={handleCompletionDeclaration}
            onCancel={() => setShowCompletionModal(false)}
          />
        </div>
      )}
    </div>
  );
};

export default UXGuidelinesManager;
