export interface Session {
    access_token: string;
    refresh_token: string;
    user: {
        id: string;
        email: string;
        [key: string]: any;
    };
    [key: string]: any;
}

export interface AuthResponse {
    result: {
        session: Session;
    };
    [key: string]: any;
}


export interface IRecentChats {
    id: string;
    current_phase: string;
    mode: string;
    asked_q: string;
    title: string;
    status: string;
    answered_count: number
    created_at: string;
}

export interface APIResponse<T> {
    success: boolean;
    message: string;
    result: T
}

export interface AngelResponse {
    success: boolean;
    message: string;
    result: {
        reply: string;
        progress: {
            phase: 'KYC' | 'BUSINESS_PLAN' | 'PLAN_TO_ROADMAP_TRANSITION' | 'ROADMAP' | 'ROADMAP_GENERATED' | 'ROADMAP_TO_IMPLEMENTATION_TRANSITION' | 'IMPLEMENTATION',
            answered: number
            total: number
            percent: number
        };
        web_search_status?: {
            is_searching: boolean;
            query?: string;
            completed?: boolean;
        };
        immediate_response?: string;
        transition_phase?: string;
        business_plan_summary?: string;
    };
}

export interface IGeneratedBP {
    success: boolean;
    message: string;
    result: {
        plan: string;
    };
}

export interface ChatResponse {
    success: boolean;
    message: string;
    result: {
        angelReply: string;
        progress?: number;
    };
}

export interface IRefreshTokenResponse {
  result: {
    session: {
      access_token: string;
      refresh_token: string;
    };
  };
}

export interface Agent {
  id: string;
  agent_type: string;
  name: string;
  description: string;
  capabilities: string[];
  expertise_areas: string[];
  expertise: string;
  research_sources: string[];
}

export interface AgentsResponse {
  success: boolean;
  agents: Agent[];
  message?: string;
}

export interface AgentGuidanceResponse {
  success: boolean;
  result: {
    guidance: string;
  };
  message?: string;
}
