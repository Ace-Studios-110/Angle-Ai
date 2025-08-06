// ChatPage.tsx
import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchBusinessPlan, fetchQuestion, fetchRoadmapPlan } from '../../services/authService';
import { toast } from 'react-toastify';
import ProgressCircle from '../../components/ProgressCircle';
import BusinessPlanModal from '../../components/BusinessPlanModal';
import VentureLoader from '../../components/VentureLoader';
import ReactMarkdown from "react-markdown";
import remarkGfm from 'remark-gfm';
import RoadmapModal from '../../components/RoadmapModal';

interface ConversationPair {
  question: string;
  answer: string;
}

interface ProgressState {
  phase: 'KYC' | 'BUSINESS_PLAN' | 'ROADMAP' | 'IMPLEMENTATION';
  answered: number;
  total: number;
  percent: number;
}

const PHASE_ORDER = ["KYC", "BUSINESS_PLAN", "ROADMAP", "IMPLEMENTATION"] as const;

const QUESTION_COUNTS = {
  KYC: 20,
  BUSINESS_PLAN: 9,
  ROADMAP: 10,
  IMPLEMENTATION: 10,
};

function getAdjustedPhaseProgress(phase: keyof typeof QUESTION_COUNTS, answered: number) {
  // Calculate how many questions came before this phase
  const currentPhaseIndex = PHASE_ORDER.indexOf(phase);
  const previousPhases = PHASE_ORDER.slice(0, currentPhaseIndex);
  const offset = previousPhases.reduce((sum, key) => sum + QUESTION_COUNTS[key], 0);

  // Calculate current step within the phase (1-based)
  const currentStep = Math.max(1, answered - offset);
  const total = QUESTION_COUNTS[phase];
  
  // Ensure currentStep doesn't exceed total for this phase
  const clampedStep = Math.min(currentStep, total);
  
  // Calculate percentage (1-100%)
  const percent = Math.max(1, Math.min(100, Math.round((clampedStep / total) * 100)));

  return {
    currentStep: clampedStep,
    total,
    percent,
  };
}

export default function ChatPage() {
  const { id: sessionId } = useParams();
  const navigate = useNavigate();
  const hasFetched = useRef(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const [history, setHistory] = useState<ConversationPair[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [currentInput, setCurrentInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<ProgressState>({
    phase: 'KYC',
    answered: 0,
    total: 20,
    percent: 0,
  });
  const [planState, setPlanState] = useState({
    showModal: false,
    loading: false,
    error: '',
    plan: '',
  });
  const [roadmapState, setRoadmapState] = useState({
    showModal: false,
    loading: false,
    error: '',
    plan: '',
  });

  const cleanQuestionText = (text: string): string => {
    return text.replace(/\[\[Q:[A-Z_]+\.\d{2}]]\s*/g, '').trim();
  };

  const formatAngelMessage = (text: string): string => {
    // Remove machine tags
    let formatted = text.replace(/\[\[Q:[A-Z_]+\.\d{2}]]\s*/g, '');
    
    // Make questions bold - look for sentences ending with ?
    formatted = formatted.replace(/([^.!?]*\?)/g, '**$1**');
    
    // Make section headers bold (like "Guiding Questions:")
    formatted = formatted.replace(/^([A-Z][a-zA-Z\s&]+:)$/gm, '**$1**');
    
    // Make numbered lists in guiding questions bold
    formatted = formatted.replace(/^(\d+\.\s)([^?\n]+\?)/gm, '$1**$2**');
    
    return formatted.trim();
  };

  // Auto-focus input after response is sent
  useEffect(() => {
    if (!loading && inputRef.current) {
      inputRef.current.focus();
    }
  }, [loading]);

  // Scroll to bottom when new messages are added
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [history, currentQuestion]);

  useEffect(() => {
    if (!sessionId || hasFetched.current) return;
    hasFetched.current = true;

    async function getInitialQuestion() {
      setLoading(true);
      try {
        const { result: { reply, progress } } = await fetchQuestion('', sessionId!);
        setCurrentQuestion(cleanQuestionText(reply));
        setProgress(progress);
      } catch (e) {
        toast.error('Failed to fetch initial question');
      } finally {
        setLoading(false);
      }
    }

    getInitialQuestion();
  }, [sessionId]);

  const handleNext = async (inputOverride?: string) => {
    const input = (inputOverride ?? currentInput).trim();
    if (!input) {
      toast.warning('Please enter your response.');
      return;
    }

    setLoading(true);
    setCurrentInput('');
    setHistory(prev => [...prev, { question: currentQuestion, answer: input }]);

    try {
      const { result: { reply, progress } } = await fetchQuestion(input, sessionId!);
      const cleaned = cleanQuestionText(reply);
      setCurrentQuestion(cleaned);
      setProgress(progress);
    } catch (e) {
      toast.error('Something went wrong.');
      setHistory(prev => prev.slice(0, -1));
      setCurrentInput(input);
    } finally {
      setLoading(false);
    }
  };

  const handleViewPlan = async () => {
    setPlanState(prev => ({ ...prev, loading: true, error: '', showModal: true }));

    try {
      const response = await fetchBusinessPlan(sessionId!);
      setPlanState(prev => ({
        ...prev,
        loading: false,
        plan: response.result.plan,
      }));
    } catch (err) {
      setPlanState(prev => ({
        ...prev,
        loading: false,
        error: (err as Error).message,
      }));
    }
  };

  const handleViewRoadmap = async () => {
    setRoadmapState(prev => ({ ...prev, loading: true, error: '', showModal: true }));

    try {
      const response = await fetchRoadmapPlan(sessionId!);
      setRoadmapState(prev => ({
        ...prev,
        loading: false,
        plan: response.result.plan,
      }));
    } catch (err) {
      setRoadmapState(prev => ({
        ...prev,
        loading: false,
        error: (err as Error).message,
      }));
    }
  };

  const { currentStep, total, percent } = getAdjustedPhaseProgress(progress.phase, progress.answered);
  const showBusinessPlanButton =
    ['ROADMAP', 'IMPLEMENTATION'].includes(progress.phase);
  
  if (loading && currentQuestion === '') return <VentureLoader title='Loading your venture' />
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-teal-50 text-sm flex flex-col">
      {/* Header Section */}
      <div className="flex-shrink-0 px-3 py-4">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-3">
            <button
              onClick={() => navigate('/ventures')}
              className="flex items-center gap-1 text-gray-600 hover:text-teal-600 transition-colors text-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Ventures
            </button>

            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-r from-teal-500 to-blue-500 rounded flex items-center justify-center text-white text-sm">🧠</div>
              <div>
                <div className="text-base font-semibold text-gray-900">{progress.phase} Phase</div>
                <div className="text-gray-500 text-xs"> Step {currentStep} of {total}</div>
              </div>
            </div>
          </div>

          <ProgressCircle
            progress={percent}
            phase={progress.phase}
          />

          {showBusinessPlanButton && (
            <div className="mt-6 flex justify-center">
              <div className="flex gap-3">
                <button
                  onClick={handleViewPlan}
                  className="group relative bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 hover:from-emerald-600 hover:via-teal-600 hover:to-cyan-600 text-white px-5 py-2.5 rounded-xl text-sm font-semibold shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-base">📊</span>
                    <span>Business Plan</span>
                  </div>
                  <div className="absolute inset-0 bg-white/20 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </button>

                <button
                  onClick={handleViewRoadmap}
                  className="group relative bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 hover:from-blue-600 hover:via-indigo-600 hover:to-purple-600 text-white px-5 py-2.5 rounded-xl text-sm font-semibold shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-base">🗺️</span>
                    <span>Roadmap Plan</span>
                  </div>
                  <div className="absolute inset-0 bg-white/20 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Modals */}
        <BusinessPlanModal
          open={planState.showModal}
          onClose={() => setPlanState(prev => ({ ...prev, showModal: false }))}
          plan={planState.plan}
          loading={planState.loading}
          error={planState.error}
        />

        <RoadmapModal
          open={roadmapState.showModal}
          onClose={() => setRoadmapState(prev => ({ ...prev, showModal: false }))}
          plan={roadmapState.plan}
          loading={roadmapState.loading}
          error={roadmapState.error}
        />
      </div>

      {/* Scrollable Chat Area */}
      <div 
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto px-3 pb-4"
        style={{ maxHeight: 'calc(100vh - 320px)' }}
      >
        <div className="max-w-4xl mx-auto space-y-4">
          {/* Chat History */}
          {history.map((pair, index) => (
            <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-100">
              <div className="p-4 border-b border-gray-100 bg-gradient-to-r from-teal-50 to-blue-50">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-gradient-to-r from-teal-500 to-blue-500 rounded flex items-center justify-center text-white text-xs">🧠</div>
                  <div className="flex-1">
                    <div className="font-semibold text-gray-800 mb-1 text-sm">Angel</div>
                    <div className="text-gray-800 whitespace-pre-wrap prose prose-sm max-w-none">
                      <ReactMarkdown rehypePlugins={[remarkGfm]}>
                        {formatAngelMessage(pair.question)}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>
              </div>
              <div className="p-4 bg-gray-50">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-gray-300 rounded flex items-center justify-center text-xs">👤</div>
                  <div className="flex-1">
                    <div className="font-semibold text-gray-800 mb-1 text-sm">You</div>
                    <div className="text-gray-700 prose prose-sm max-w-none">
                      <ReactMarkdown rehypePlugins={[remarkGfm]}>
                        {pair.answer}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}

          {/* Current Question */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-100">
            <div className="p-4 border-b border-gray-100 bg-gradient-to-r from-teal-50 to-blue-50">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 bg-gradient-to-r from-teal-500 to-blue-500 rounded flex items-center justify-center text-white text-xs">🧠</div>
                <div className="flex-1">
                  <div className="font-semibold text-gray-800 mb-1 text-sm">Angel</div>
                  <div className="text-gray-800 whitespace-pre-wrap">
                    {loading ? (
                      <div className="flex items-center gap-2">
                        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-teal-500"></div>
                        <span className="text-teal-600 text-xs">Angel is thinking...</span>
                      </div>
                    ) : (
                      currentQuestion || 'Loading...'
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Fixed Input Area */}
      <div className="flex-shrink-0 bg-gradient-to-br from-slate-50 to-teal-50 px-3 py-3">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow-lg border border-white/50 p-3">
            <div className="flex items-center gap-3">
              <div className="w-7 h-7 bg-gray-300 rounded-full flex items-center justify-center text-xs flex-shrink-0">👤</div>
              <div className="flex-1 min-w-0">
                <textarea
                  ref={inputRef}
                  className="w-full rounded-lg p-2.5 resize-none text-sm bg-gray-50 text-gray-900 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent focus:bg-white transition-all duration-200 placeholder-gray-500"
                  rows={1}
                  value={currentInput}
                  onChange={(e) => setCurrentInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleNext();
                    }
                  }}
                  placeholder="Type your response... (Enter to send)"
                  disabled={loading}
                  style={{ minHeight: '38px', maxHeight: '120px' }}
                  onInput={(e) => {
                    const target = e.target as HTMLTextAreaElement;
                    target.style.height = 'auto';
                    target.style.height = Math.min(target.scrollHeight, 120) + 'px';
                  }}
                />
              </div>
              <button
                className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white p-2.5 rounded-lg font-medium text-sm disabled:opacity-50 shadow-md transition-all duration-200 flex-shrink-0"
                onClick={() => handleNext()}
                disabled={loading || !currentInput.trim()}
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                )}
              </button>
            </div>
            
            {/* Quick Actions Row */}
            {progress.phase !== 'KYC' && (
              <div className="flex items-center justify-between mt-2.5">
                <div className="flex gap-1.5">
                  {['Support', 'Draft', 'Scrapping'].map(cmd => (
                    <button
                      key={cmd}
                      className="bg-gray-100 hover:bg-teal-100 text-gray-600 hover:text-teal-700 px-2.5 py-1 rounded-md text-xs font-medium disabled:opacity-50 transition-colors duration-200"
                      onClick={() => handleNext(cmd)}
                      disabled={loading}
                    >
                      {cmd}
                    </button>
                  ))}
                </div>
                <p className="text-gray-400 text-xs">
                  💡 Quick actions or type detailed response
                </p>
              </div>
            )}
            
            {progress.phase === 'KYC' && (
              <div className="mt-2.5">
                <p className="text-gray-400 text-xs text-center">
                  💡 Press Enter to send or Shift+Enter for new line
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}