"use client";

// ChatPage.tsx
import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  fetchBusinessPlan,
  fetchQuestion,
  fetchRoadmapPlan,
  uploadBusinessPlan,
} from "../../services/authService";
import { toast } from "react-toastify";
import ProgressCircle from "../../components/ProgressCircle";
import BusinessPlanModal from "../../components/BusinessPlanModal";
import VentureLoader from "../../components/VentureLoader";
import RoadmapModal from "../../components/RoadmapModal";
import QuestionNavigator from "../../components/QuestionNavigator";
import SmartInput from "../../components/SmartInput";
import AcceptModifyButtons from "../../components/AcceptModifyButtons";
import WebSearchIndicator from "../../components/WebSearchIndicator";
import PlanToRoadmapTransition from "../../components/PlanToRoadmapTransition";
import ModifyModal from "../../components/ModifyModal";
import RoadmapDisplay from "../../components/RoadmapDisplay";
import RoadmapToImplementationTransition from "../../components/RoadmapToImplementationTransition";
import Implementation from "../Implementation";
import RoadmapEditModal from "../../components/RoadmapEditModal";

interface ConversationPair {
  question: string;
  answer: string;
}

interface ProgressState {
  phase: "KYC" | "BUSINESS_PLAN" | "PLAN_TO_ROADMAP_TRANSITION" | "ROADMAP" | "ROADMAP_GENERATED" | "ROADMAP_TO_IMPLEMENTATION_TRANSITION" | "IMPLEMENTATION";
  answered: number;
  total: number;
  percent: number;
}

// Updated to include PLAN_TO_ROADMAP_TRANSITION phase

const QUESTION_COUNTS = {
  KYC: 20,
  BUSINESS_PLAN: 46,
  ROADMAP: 1,
  IMPLEMENTATION: 10,
};


export default function ChatPage() {
  const { id: sessionId } = useParams();
  const navigate = useNavigate();
  const hasFetched = useRef(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const [history, setHistory] = useState<ConversationPair[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [currentInput, setCurrentInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showMobileNav, setShowMobileNav] = useState(false);
  const [progress, setProgress] = useState<ProgressState>({
    phase: "KYC",
    answered: 0,
    total: 20,
    percent: 0,
  });

  // Console logging for progress debugging
  useEffect(() => {
    console.log("🔄 Progress State Updated:", {
      phase: progress.phase,
      answered: progress.answered,
      total: progress.total,
      percent: progress.percent,
      timestamp: new Date().toISOString()
    });
  }, [progress]);

  // Check if current question is a verification message
  useEffect(() => {
    if (currentQuestion) {
      const isVerification = isVerificationMessage(currentQuestion);
      setShowVerificationButtons(isVerification);
      console.log("🔍 Verification Check:", { 
        currentQuestion: currentQuestion.substring(0, 100) + "...", 
        isVerification 
      });
    }
  }, [currentQuestion]);
  const [planState, setPlanState] = useState({
    showModal: false,
    loading: false,
    error: "",
    plan: "",
  });
  const [showVerificationButtons, setShowVerificationButtons] = useState(false);
  const [webSearchStatus, setWebSearchStatus] = useState<{
    is_searching: boolean;
    query?: string;
    completed?: boolean;
  }>({
    is_searching: false,
    query: undefined,
    completed: false
  });
  const [transitionData, setTransitionData] = useState<{
    businessPlanSummary: string;
    transitionPhase: string;
  } | null>(null);
  const [modifyModal, setModifyModal] = useState<{
    isOpen: boolean;
    currentText: string;
  }>({
    isOpen: false,
    currentText: ""
  });
  const [roadmapData, setRoadmapData] = useState<{
    roadmapContent: string;
    isGenerated: boolean;
  } | null>(null);
  const [roadmapToImplementationTransition, setRoadmapToImplementationTransition] = useState<{
    roadmapContent: string;
    isActive: boolean;
  } | null>(null);
  const [roadmapEditModal, setRoadmapEditModal] = useState<{
    isOpen: boolean;
    roadmapContent: string;
  }>({
    isOpen: false,
    roadmapContent: ""
  });

  // Function to detect if the current message is a verification request
  const isVerificationMessage = (message: string): boolean => {
    const verificationKeywords = [
      "does this look accurate",
      "does this look correct",
      "is this accurate",
      "is this correct",
      "please let me know where you'd like to modify",
      "here's what i've captured so far"
    ];
    
    const lowerMessage = message.toLowerCase();
    return verificationKeywords.some(keyword => lowerMessage.includes(keyword));
  };

  // Handle Accept button click
  const handleAccept = async () => {
    setShowVerificationButtons(false);
    setLoading(true);
    
    try {
      const {
        result: { reply, progress, web_search_status, immediate_response },
      } = await fetchQuestion("Accept", sessionId!);
      const formatted = formatAngelMessage(reply);
      setCurrentQuestion(formatted);
      setProgress(progress);
      setWebSearchStatus(web_search_status || { is_searching: false, query: undefined, completed: false });
      
      // Show immediate response if available
      if (immediate_response) {
        toast.info(immediate_response, { 
          autoClose: 5000,
          position: "top-center",
          className: "bg-blue-50 border border-blue-200 text-blue-800"
        });
      }
    } catch (error) {
      console.error("Failed to fetch question:", error);
      toast.error("Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  // Handle Modify button click
  const handleModify = (currentText: string) => {
    setModifyModal({
      isOpen: true,
      currentText: currentText
    });
  };

  // Handle saving modified text
  const handleModifySave = async (modifiedText: string) => {
    setModifyModal(prev => ({ ...prev, isOpen: false }));
    setShowVerificationButtons(false);
    
    try {
      setLoading(true);
      await handleNext(modifiedText);
    } catch (error) {
      console.error("Error sending modified text:", error);
      toast.error("Failed to send modifications. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Handle starting implementation (triggers roadmap to implementation transition)
  const handleStartImplementation = async () => {
    try {
      setLoading(true);
      toast.info("Preparing implementation transition...");
      
      // Call the roadmap to implementation transition endpoint
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/angel/sessions/${sessionId}/roadmap-to-implementation-transition`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('sb_access_token')}`
        }
      });

      const data = await response.json();
      
      if (data.success) {
        toast.success("Implementation transition prepared!");
        setRoadmapData(null);
        setProgress(data.result.progress);
        
        // Set the roadmap to implementation transition
        setRoadmapToImplementationTransition({
          roadmapContent: data.result.reply,
          isActive: true
        });
      } else {
        toast.error(data.message || "Failed to prepare implementation transition");
      }
    } catch (error) {
      console.error("Error preparing implementation transition:", error);
      toast.error("Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  // Handle actual implementation start (from transition screen)
  const handleActualStartImplementation = async () => {
    try {
      setLoading(true);
      toast.info("Starting implementation phase...");
      
      // Call the start implementation endpoint
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/angel/sessions/${sessionId}/start-implementation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('sb_access_token')}`
        }
      });

      const data = await response.json();
      
      if (data.success) {
        toast.success("Implementation phase activated!");
        setRoadmapToImplementationTransition(null);
        setProgress(data.result.progress);
        
        // Set the first implementation question
        const formatted = formatAngelMessage(data.result.reply);
        setCurrentQuestion(formatted);
      } else {
        toast.error(data.message || "Failed to start implementation");
      }
    } catch (error) {
      console.error("Error starting implementation:", error);
      toast.error("Something went wrong.");
    } finally {
      setLoading(false);
    }
  };
  const [roadmapState, setRoadmapState] = useState({
    showModal: false,
    loading: false,
    error: "",
    plan: "",
  });

  // const cleanQuestionText = (text: string): string => {
  //   return text.replace(/\[\[Q:[A-Z_]+\.\d{2}]]\s*/g, "").trim();
  // };

  const formatAngelMessage = (text: string): string => {
    // Remove machine tags
    let formatted = text.replace(/\[\[Q:[A-Z_]+\.\d{2}]]\s*/g, "");

    // Remove ALL asterisks (single, double, triple, etc.)
    formatted = formatted.replace(/\*+/g, "");

    // Remove ALL hashes
    formatted = formatted.replace(/#+/g, "");

    // Remove ALL dashes and similar symbols at start of lines or standalone
    formatted = formatted.replace(/^[-–—•]+\s*/gm, "");
    formatted = formatted.replace(/[-–—]{2,}/g, "");

    // Clean up bullet points - replace with simple dash
    formatted = formatted.replace(/^[•\-–—*]\s+/gm, "- ");

    // Clean up numbered lists - keep simple format
    formatted = formatted.replace(/^(\d+)\.\s+/gm, "$1. ");

    // Remove any remaining standalone formatting symbols
    formatted = formatted.replace(/^[*#\-–—•]+\s*$/gm, "");

    // Clean up excessive whitespace
    formatted = formatted.replace(/\n{3,}/g, "\n\n");
    formatted = formatted.replace(/\s{3,}/g, " ");

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
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  }, [history, currentQuestion]);

  useEffect(() => {
    if (!sessionId || hasFetched.current) return;
    hasFetched.current = true;

    async function getInitialQuestion() {
      setLoading(true);
      try {
        const {
          result: { reply, progress, web_search_status, immediate_response },
        } = await fetchQuestion("", sessionId!);
        console.log("📥 Initial Question API Response:", {
          reply: reply.substring(0, 100) + "...",
          progress: progress,
          sessionId: sessionId,
          web_search_status: web_search_status,
          immediate_response: immediate_response
        });
        setCurrentQuestion(formatAngelMessage(reply));
        setProgress(progress);
        setWebSearchStatus(web_search_status || { is_searching: false, query: undefined, completed: false });
        
        // Show immediate response if available
        if (immediate_response) {
          toast.info(immediate_response, { autoClose: 5000 });
        }
      } catch (error) {
        console.error("Failed to fetch initial question:", error);
        toast.error("Failed to fetch initial question");
      } finally {
        setLoading(false);
      }
    }

    getInitialQuestion();
  }, [sessionId]);

  const handleNext = async (inputOverride?: string) => {
    const input = (inputOverride ?? currentInput).trim();
    if (!input) {
      toast.warning("Please enter your response.");
      return;
    }

    setLoading(true);
    setCurrentInput("");
    setHistory((prev) => [
      ...prev,
      { question: currentQuestion, answer: input },
    ]);

    try {
      const {
        result: { reply, progress, web_search_status, immediate_response, transition_phase, business_plan_summary },
      } = await fetchQuestion(input, sessionId!);
      console.log("📥 Question API Response:", {
        input: input,
        reply: reply.substring(0, 100) + "...",
        progress: progress,
        sessionId: sessionId,
        web_search_status: web_search_status,
        immediate_response: immediate_response,
        transition_phase: transition_phase,
        business_plan_summary: business_plan_summary ? "Present" : "None"
      });
      
      // Handle transition phases
      if (transition_phase === "PLAN_TO_ROADMAP") {
        setTransitionData({
          businessPlanSummary: business_plan_summary || "",
          transitionPhase: transition_phase
        });
        setProgress(progress);
        return;
      }
      
      // Handle roadmap generation
      if (transition_phase === "ROADMAP_GENERATED") {
        setRoadmapData({
          roadmapContent: reply,
          isGenerated: true
        });
        setProgress(progress);
        return;
      }
      
      const formatted = formatAngelMessage(reply);
      setCurrentQuestion(formatted);
      setProgress(progress);
      setWebSearchStatus(web_search_status || { is_searching: false, query: undefined, completed: false });
      
      // Show immediate response if available
      if (immediate_response) {
        toast.info(immediate_response, { 
          autoClose: 5000,
          position: "top-center",
          className: "bg-blue-50 border border-blue-200 text-blue-800"
        });
      }
    } catch (error) {
      console.error("Failed to fetch question:", error);
      toast.error("Something went wrong.");
      setHistory((prev) => prev.slice(0, -1));
      setCurrentInput(input);
    } finally {
      setLoading(false);
    }
  };

  const handleViewPlan = async () => {
    setPlanState((prev) => ({
      ...prev,
      loading: true,
      error: "",
      showModal: true,
    }));

    try {
      const response = await fetchBusinessPlan(sessionId!);
      setPlanState((prev) => ({
        ...prev,
        loading: false,
        plan: response.result.plan,
      }));
    } catch (err) {
      setPlanState((prev) => ({
        ...prev,
        loading: false,
        error: (err as Error).message,
      }));
    }
  };

  const handleViewRoadmap = async () => {
    setRoadmapState((prev) => ({
      ...prev,
      loading: true,
      error: "",
      showModal: true,
    }));

    try {
      const response = await fetchRoadmapPlan(sessionId!);
      setRoadmapState((prev) => ({
        ...prev,
        loading: false,
        plan: response.result.plan,
      }));
    } catch (err) {
      setRoadmapState((prev) => ({
        ...prev,
        loading: false,
        error: (err as Error).message,
      }));
    }
  };

  const handleEditPlan = () => {
    // Close the business plan modal and allow editing
    setPlanState(prev => ({ ...prev, showModal: false }));
    toast.info("Business Plan editing mode activated. You can now modify your responses.");
  };

  const handleEditRoadmap = () => {
    // Open the roadmap edit modal
    if (roadmapData && roadmapData.roadmapContent) {
      setRoadmapEditModal({
        isOpen: true,
        roadmapContent: roadmapData.roadmapContent
      });
      // Close the roadmap modal
      setRoadmapState(prev => ({ ...prev, showModal: false }));
    } else {
      toast.error("No roadmap content available to edit");
    }
  };

  const handleSaveEditedRoadmap = async (updatedContent: string) => {
    try {
      toast.info("Saving roadmap changes...");
      
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/roadmap/sessions/${sessionId}/update-roadmap`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          updated_content: updatedContent
        })
      });

      if (!response.ok) {
        throw new Error('Failed to save roadmap');
      }

      const data = await response.json();
      
      if (data.success) {
        // Update local roadmap data
        setRoadmapData(prev => prev ? {
          ...prev,
          roadmapContent: updatedContent
        } : null);
        
        // Close edit modal
        setRoadmapEditModal({
          isOpen: false,
          roadmapContent: ""
        });
        
        toast.success("Roadmap saved successfully!");
      } else {
        toast.error(data.message || "Failed to save roadmap");
      }
    } catch (error) {
      console.error("Error saving roadmap:", error);
      toast.error("Failed to save roadmap");
    }
  };

  const handleUploadPlan = async (file: File) => {
    try {
      toast.info(`Uploading ${file.name}...`);
      
      const response = await uploadBusinessPlan(sessionId!, file);
      
      if (response.success) {
        toast.success(`${file.name} uploaded successfully!`);
        
        // Add the upload message to chat history
        if (response.chat_message) {
          setHistory(prev => [...prev, {
            question: "",
            answer: response.chat_message!
          }]);
        }
        
        // Refresh the current question to show the upload response
        await fetchQuestion(sessionId!, "");
        
      } else {
        toast.error(response.error || "Upload failed");
      }

    } catch (error) {
      toast.error("Failed to upload file. Please try again.");
      console.error("Upload error:", error);
    }
  };

  const handleApprovePlan = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/angel/sessions/${sessionId}/transition-decision`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('sb_access_token')}`
        },
        body: JSON.stringify({ decision: 'approve' })
      });

      const data = await response.json();
      
      if (data.success) {
        toast.success("Plan approved! Generating roadmap...");
        setTransitionData(null);
        setProgress(data.result.progress);
        
        // Navigate to roadmap phase
        if (data.result.roadmap) {
          setRoadmapData({
            roadmapContent: data.result.roadmap,
            isGenerated: true
          });
          console.log("Roadmap generated:", data.result.roadmap);
        }
      } else {
        toast.error(data.message || "Failed to approve plan");
      }
    } catch (error) {
      console.error("Failed to approve plan:", error);
      toast.error("Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const handleRevisitPlan = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/angel/sessions/${sessionId}/transition-decision`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('sb_access_token')}`
        },
        body: JSON.stringify({ decision: 'revisit' })
      });

      const data = await response.json();
      
      if (data.success) {
        toast.success("Plan review mode activated");
        setTransitionData(null);
        setProgress(data.result.progress);
        
        // Refresh to get the first business plan question
        await fetchQuestion("", sessionId!);
      } else {
        toast.error(data.message || "Failed to activate review mode");
      }
    } catch (error) {
      console.error("Failed to revisit plan:", error);
      toast.error("Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  // Use backend progress data directly to avoid calculation mismatches
  const currentStep = progress.answered || 1;
  const total = progress.total || QUESTION_COUNTS[progress.phase as keyof typeof QUESTION_COUNTS];
  const percent = progress.percent || 1;

  // Console logging for calculated display values
  console.log("📊 Display Values Calculated:", {
    currentStep: currentStep,
    total: total,
    percent: percent,
    progressPhase: progress.phase,
    progressAnswered: progress.answered,
    progressTotal: progress.total,
    progressPercent: progress.percent,
    questionCounts: QUESTION_COUNTS
  });
  const showBusinessPlanButton = ["ROADMAP", "IMPLEMENTATION"].includes(
    progress.phase
  );

  if (loading && currentQuestion === "")
    return <VentureLoader title="Loading your venture" />;

  // Show transition component if in transition phase
  if (transitionData && transitionData.transitionPhase === "PLAN_TO_ROADMAP") {
    return (
      <PlanToRoadmapTransition
        businessPlanSummary={transitionData.businessPlanSummary}
        onApprove={handleApprovePlan}
        onRevisit={handleRevisitPlan}
        loading={loading}
      />
    );
  }

  // Show roadmap display if roadmap is generated
  if (roadmapData && roadmapData.isGenerated) {
    return (
      <RoadmapDisplay
        roadmapContent={roadmapData.roadmapContent}
        onStartImplementation={handleStartImplementation}
        onEditRoadmap={handleEditRoadmap}
        loading={loading}
      />
    );
  }

  // Show roadmap to implementation transition
  if (roadmapToImplementationTransition && roadmapToImplementationTransition.isActive) {
    return (
      <RoadmapToImplementationTransition
        roadmapContent={roadmapToImplementationTransition.roadmapContent}
        onStartImplementation={handleActualStartImplementation}
        loading={loading}
      />
    );
  }

  // Show implementation phase
  if (progress.phase === "IMPLEMENTATION") {
    // Create session data object for implementation
    const sessionData = {
      sessionId: sessionId!,
      currentPhase: progress.phase,
      businessName: "Your Business", // This would come from session data
      industry: "General Business", // This would come from session data
      location: "United States", // This would come from session data
      businessType: "Startup" // This would come from session data
    };

    return (
      <Implementation
        sessionId={sessionId!}
        sessionData={sessionData}
        onPhaseChange={(phase) => {
          // Handle phase changes if needed
          console.log('Phase changed to:', phase);
        }}
      />
    );
  }

  // Transform history into questions array
  const questions = history.map((pair, index) => ({
    id: `${progress.phase}.${index + 1}`,
    phase: progress.phase,
    number: index + 1,
    title: pair.question,
    completed: true,
  }));

  // Add current question
  if (currentQuestion) {
    questions.push({
      id: `${progress.phase}.${questions.length + 1}`,
      phase: progress.phase,
      number: questions.length + 1,
      title: currentQuestion,
      completed: false,
    });
  }

  // Console logging for question tracking
  console.log("❓ Question Tracking:", {
    historyLength: history.length,
    currentQuestion: currentQuestion ? currentQuestion.substring(0, 50) + "..." : "None",
    totalQuestions: questions.length,
    questions: questions.map(q => ({ id: q.id, number: q.number, completed: q.completed }))
  });

  const handleQuestionSelect = async (questionId: string) => {
    const numberStr = questionId.split(".")[1];
    const number = Number.parseInt(numberStr) - 1;
    if (number < history.length) {
      // Navigate to a previous question
      const pair = history[number];
      setCurrentQuestion(pair.question);
      // TODO: Implement API call to actually navigate to this question
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-teal-50 text-sm flex flex-col lg:flex-row">
      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header Section */}
        <div className="flex-shrink-0 px-3 py-4 lg:px-3 lg:py-4">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-center justify-between mb-3">
              <button
                onClick={() => navigate("/ventures")}
                className="flex items-center gap-1 text-gray-600 hover:text-teal-600 transition-colors text-sm"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
                <span className="hidden sm:inline">Back to Ventures</span>
                <span className="sm:hidden">Back</span>
              </button>

              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-r from-teal-500 to-blue-500 rounded flex items-center justify-center text-white text-sm">
                  🧭
                </div>
                <div className="hidden sm:block">
                  <div className="text-base font-semibold text-gray-900">
                    {progress.phase} Phase
                  </div>
                  <div className="text-gray-500 text-xs">
                    {" "}
                    Step {currentStep} of {total}
                  </div>
                </div>
                <div className="sm:hidden">
                  <div className="text-sm font-semibold text-gray-900">
                    {progress.phase}
                  </div>
                  <div className="text-gray-500 text-xs">
                    {currentStep}/{total}
                  </div>
                </div>
              </div>

              {/* Mobile Navigation Toggle */}
              <button
                onClick={() => setShowMobileNav(!showMobileNav)}
                className="lg:hidden p-2 rounded-lg bg-white/80 backdrop-blur-sm border border-gray-200 hover:bg-white transition-colors"
              >
                <svg
                  className="w-5 h-5 text-gray-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                </svg>
              </button>
            </div>

            <ProgressCircle progress={percent} phase={progress.phase} />

            {showBusinessPlanButton && (
              <div className="mt-6 flex justify-center">
                <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
                  <button
                    onClick={handleViewPlan}
                    className="group relative bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 hover:from-emerald-600 hover:via-teal-600 hover:to-cyan-600 text-white px-4 sm:px-5 py-2.5 rounded-xl text-sm font-semibold shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 w-full sm:w-auto"
                  >
                    <div className="flex items-center justify-center sm:justify-start gap-2">
                      <span className="text-base">📊</span>
                      <span>Business Plan</span>
                    </div>
                    <div className="absolute inset-0 bg-white/20 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  </button>

                  <button
                    onClick={handleViewRoadmap}
                    className="group relative bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 hover:from-blue-600 hover:via-indigo-600 hover:to-purple-600 text-white px-4 sm:px-5 py-2.5 rounded-xl text-sm font-semibold shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 w-full sm:w-auto"
                  >
                    <div className="flex items-center justify-center sm:justify-start gap-2">
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
            onClose={() =>
              setPlanState((prev) => ({ ...prev, showModal: false }))
            }
            plan={planState.plan}
            loading={planState.loading}
            error={planState.error}
            onEditPlan={handleEditPlan}
          />

          <RoadmapModal
            open={roadmapState.showModal}
            onClose={() =>
              setRoadmapState((prev) => ({ ...prev, showModal: false }))
            }
            plan={roadmapState.plan}
            loading={roadmapState.loading}
            error={roadmapState.error}
            onEditRoadmap={handleEditRoadmap}
          />
        </div>

        {/* Scrollable Chat Area */}
        <div
          ref={chatContainerRef}
          className="flex-1 overflow-y-auto px-3 pb-4 lg:pb-4"
          style={{ 
            maxHeight: "calc(100vh - 320px)",
            minHeight: "calc(100vh - 320px)"
          }}
        >
          <div className="max-w-4xl mx-auto space-y-4">
            {/* Chat History */}
            {history.map((pair, index) => (
              <div
                key={index}
                className="bg-white rounded-lg shadow-sm border border-gray-100"
              >
                <div className="p-3 sm:p-4 border-b border-gray-100 bg-gradient-to-r from-teal-50 to-blue-50">
                  <div className="flex items-start gap-2 sm:gap-3">
                    <div className="w-6 h-6 bg-gradient-to-r from-teal-500 to-blue-500 rounded flex items-center justify-center text-white text-xs flex-shrink-0">
                      🧭
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-gray-800 mb-1 text-sm">
                        Angel
                      </div>
                      <div className="text-gray-800 whitespace-pre-wrap text-sm">
                        {formatAngelMessage(pair.question)}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="p-3 sm:p-4 bg-gray-50">
                  <div className="flex items-start gap-2 sm:gap-3">
                    <div className="w-6 h-6 bg-gray-300 rounded flex items-center justify-center text-xs flex-shrink-0">
                      👤
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-gray-800 mb-1 text-sm">
                        You
                      </div>
                      <div className="text-gray-700 whitespace-pre-wrap text-sm">
                        {pair.answer}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {/* Current Question */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-100">
              <div className="p-3 sm:p-4 border-b border-gray-100 bg-gradient-to-r from-teal-50 to-blue-50">
                <div className="flex items-start gap-2 sm:gap-3">
                  <div className="w-6 h-6 bg-gradient-to-r from-teal-500 to-blue-500 rounded flex items-center justify-center text-white text-xs flex-shrink-0">
                    🧭
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-gray-800 mb-1 text-sm">
                      Angel
                    </div>
                    <div className="text-gray-800 whitespace-pre-wrap text-sm">
                      {loading ? (
                        <div className="flex items-center gap-2">
                          <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-teal-500"></div>
                          <span className="text-teal-600 text-xs">
                            Angel is thinking...
                          </span>
                        </div>
                      ) : (
                        currentQuestion || "Loading..."
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
            {/* Web Search Progress Indicator */}
            <WebSearchIndicator 
              isSearching={webSearchStatus.is_searching} 
              searchQuery={webSearchStatus.query} 
            />

            {/* Accept/Modify Buttons for Verification */}
            {showVerificationButtons && !loading && (
              <div className="mb-4">
                <AcceptModifyButtons
                  onAccept={handleAccept}
                  onModify={handleModify}
                  disabled={loading}
                  currentText={currentQuestion}
                />
              </div>
            )}
            
            <SmartInput
              value={currentInput}
              onChange={setCurrentInput}
              onSubmit={handleNext}
              placeholder="Type your response... (Enter to send)"
              disabled={loading}
              loading={loading}
              currentQuestion={currentQuestion}
            />

            {/* Quick Actions Row */}
            {progress.phase !== "KYC" && (
              <div className="mt-4">
                <div className="text-center mb-3">
                  <p className="text-gray-500 text-sm font-medium">🚀 Quick Actions</p>
                  <p className="text-gray-400 text-xs">Choose a tool to help with your response</p>
                </div>
                
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                  {/* Support Button */}
                  <button
                    onClick={() => handleNext("Support")}
                    disabled={loading}
                    className="group relative bg-gradient-to-br from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 border border-blue-200 hover:border-blue-300 rounded-xl p-4 transition-all duration-300 transform hover:scale-105 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    <div className="flex flex-col items-center space-y-2">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-lg group-hover:scale-110 transition-transform duration-300">
                        💬
                      </div>
                      <div className="text-center">
                        <div className="text-sm font-semibold text-blue-800 group-hover:text-blue-900">Support</div>
                        <div className="text-xs text-blue-600 group-hover:text-blue-700">Get guided help</div>
                      </div>
                </div>
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-indigo-500/10 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  </button>

                  {/* Draft Button */}
                <button
                    onClick={() => handleNext("Draft")}
                    disabled={loading}
                    className="group relative bg-gradient-to-br from-emerald-50 to-green-50 hover:from-emerald-100 hover:to-green-100 border border-emerald-200 hover:border-emerald-300 rounded-xl p-4 transition-all duration-300 transform hover:scale-105 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    <div className="flex flex-col items-center space-y-2">
                      <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-green-600 rounded-full flex items-center justify-center text-white text-lg group-hover:scale-110 transition-transform duration-300">
                        ✍️
                      </div>
                      <div className="text-center">
                        <div className="text-sm font-semibold text-emerald-800 group-hover:text-emerald-900">Draft</div>
                        <div className="text-xs text-emerald-600 group-hover:text-emerald-700">Generate content</div>
                      </div>
                    </div>
                    <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-green-500/10 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  </button>

                  {/* Scrapping Button */}
                  <button
                    onClick={() => handleNext("Scrapping")}
                    disabled={loading}
                    className="group relative bg-gradient-to-br from-orange-50 to-amber-50 hover:from-orange-100 hover:to-amber-100 border border-orange-200 hover:border-orange-300 rounded-xl p-4 transition-all duration-300 transform hover:scale-105 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    <div className="flex flex-col items-center space-y-2">
                      <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-amber-600 rounded-full flex items-center justify-center text-white text-lg group-hover:scale-110 transition-transform duration-300">
                        🔧
                      </div>
                      <div className="text-center">
                        <div className="text-sm font-semibold text-orange-800 group-hover:text-orange-900">Scrapping</div>
                        <div className="text-xs text-orange-600 group-hover:text-orange-700">Polish ideas</div>
                      </div>
                    </div>
                    <div className="absolute inset-0 bg-gradient-to-br from-orange-500/10 to-amber-500/10 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </button>

                  {/* Kickstart Button */}
                  <button
                    onClick={() => handleNext("Kickstart")}
                    disabled={loading}
                    className="group relative bg-gradient-to-br from-purple-50 to-violet-50 hover:from-purple-100 hover:to-violet-100 border border-purple-200 hover:border-purple-300 rounded-xl p-4 transition-all duration-300 transform hover:scale-105 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    <div className="flex flex-col items-center space-y-2">
                      <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-violet-600 rounded-full flex items-center justify-center text-white text-lg group-hover:scale-110 transition-transform duration-300">
                        🚀
                      </div>
                      <div className="text-center">
                        <div className="text-sm font-semibold text-purple-800 group-hover:text-purple-900">Kickstart</div>
                        <div className="text-xs text-purple-600 group-hover:text-purple-700">Get templates</div>
                      </div>
              </div>
                    <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-violet-500/10 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  </button>

                  {/* Who do I contact? Button */}
                      <button
                    onClick={() => handleNext("Who do I contact?")}
                        disabled={loading}
                    className="group relative bg-gradient-to-br from-teal-50 to-cyan-50 hover:from-teal-100 hover:to-cyan-100 border border-teal-200 hover:border-teal-300 rounded-xl p-4 transition-all duration-300 transform hover:scale-105 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    <div className="flex flex-col items-center space-y-2">
                      <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-cyan-600 rounded-full flex items-center justify-center text-white text-lg group-hover:scale-110 transition-transform duration-300">
                        👥
                      </div>
                      <div className="text-center">
                        <div className="text-sm font-semibold text-teal-800 group-hover:text-teal-900">Contact</div>
                        <div className="text-xs text-teal-600 group-hover:text-teal-700">Find experts</div>
                      </div>
                    </div>
                    <div className="absolute inset-0 bg-gradient-to-br from-teal-500/10 to-cyan-500/10 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                      </button>
                  </div>

                <div className="mt-3 text-center">
                  <p className="text-gray-400 text-xs">
                    💡 Or type your detailed response below
                  </p>
                </div>
                </div>
              )}

              {progress.phase === "KYC" && (
                <div className="mt-2.5">
                  <p className="text-gray-400 text-xs text-center">
                    💡 Press Enter to send or Shift+Enter for new line
                  </p>
                </div>
              )}
          </div>
        </div>
      </div>

      {/* Right Navigation Panel - Desktop */}
      <div className="hidden lg:block w-80 flex-shrink-0 border-l border-gray-200 h-screen sticky top-0 overflow-y-auto">
        <QuestionNavigator
          questions={questions}
          currentPhase={progress.phase}
          onQuestionSelect={handleQuestionSelect}
          currentProgress={progress}
          onEditPlan={handleEditPlan}
          onUploadPlan={handleUploadPlan}
        />
      </div>

      {/* Mobile Navigation Panel - Overlay */}
      {showMobileNav && (
        <div className="lg:hidden fixed inset-0 z-50">
          {/* Backdrop */}
          <div 
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setShowMobileNav(false)}
          />
          
          {/* Navigation Panel */}
          <div className="absolute right-0 top-0 h-full w-full max-w-sm bg-white shadow-2xl transform transition-transform duration-300 ease-in-out overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-teal-50 to-blue-50">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-r from-teal-500 to-blue-500 rounded flex items-center justify-center text-white text-sm">
                  🧭
                </div>
                <h3 className="text-lg font-semibold text-gray-900">Questions</h3>
              </div>
              <button
                onClick={() => setShowMobileNav(false)}
                className="p-2 rounded-lg hover:bg-white/80 transition-colors"
              >
                <svg
                  className="w-6 h-6 text-gray-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
            
            <div className="h-full flex flex-col">
              {/* Progress Summary */}
              <div className="p-4 border-b border-gray-100 bg-white">
                <div className="text-center">
                  <div className="text-sm font-medium text-gray-600 mb-1">Current Progress</div>
                  <div className="text-lg font-bold text-gray-900">{progress.phase}</div>
                  <div className="text-sm text-gray-500">Step {currentStep} of {total}</div>
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-teal-500 to-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${percent}%` }}
                    ></div>
                  </div>
                </div>
              </div>
              
              {/* Questions List - Scrollable Area */}
              <div className="flex-1 overflow-y-auto px-4 py-2">
                <div className="space-y-3">
                  {questions.map((question) => (
                    <div
                      key={question.id}
                      className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 ${
                        question.completed
                          ? 'bg-green-50 border-green-200 hover:bg-green-100'
                          : 'bg-blue-50 border-blue-200 hover:bg-blue-100'
                      }`}
                      onClick={() => {
                        handleQuestionSelect(question.id);
                        setShowMobileNav(false);
                      }}
                    >
                      <div className="flex items-start gap-2">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs text-white flex-shrink-0 ${
                          question.completed
                            ? 'bg-green-500'
                            : 'bg-blue-500'
                        }`}>
                          {question.completed ? '✓' : '?'}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-xs text-gray-500 mb-1">
                            {question.phase} • Q{question.number}
                          </div>
                          <div className="text-sm font-medium text-gray-900 line-clamp-3">
                            {question.title}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Bottom Actions */}
              <div className="p-4 border-t border-gray-100 bg-gray-50 space-y-3">
                {showBusinessPlanButton && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        handleViewPlan();
                        setShowMobileNav(false);
                      }}
                      className="flex-1 bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-3 py-2.5 rounded-lg text-sm font-medium hover:from-emerald-600 hover:to-teal-600 transition-colors"
                    >
                      📊 Plan
                    </button>
                    <button
                      onClick={() => {
                        handleViewRoadmap();
                        setShowMobileNav(false);
                      }}
                      className="flex-1 bg-gradient-to-r from-blue-500 to-indigo-500 text-white px-3 py-2.5 rounded-lg text-sm font-medium hover:from-blue-600 hover:to-indigo-600 transition-colors"
                    >
                      🗺️ Roadmap
                    </button>
                  </div>
                )}
                <button
                  onClick={() => setShowMobileNav(false)}
                  className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modify Modal */}
      <ModifyModal
        isOpen={modifyModal.isOpen}
        onClose={() => setModifyModal(prev => ({ ...prev, isOpen: false }))}
        currentText={modifyModal.currentText}
        onSave={handleModifySave}
        loading={loading}
      />

      {/* Roadmap Edit Modal */}
      <RoadmapEditModal
        isOpen={roadmapEditModal.isOpen}
        onClose={() => setRoadmapEditModal(prev => ({ ...prev, isOpen: false }))}
        roadmapContent={roadmapEditModal.roadmapContent}
        sessionId={sessionId!}
        onSave={handleSaveEditedRoadmap}
        loading={loading}
      />
    </div>
  );
}
