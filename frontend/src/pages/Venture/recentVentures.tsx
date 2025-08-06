import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import type { IRecentChats } from '../../types/apiTypes';
import { fetchSessions } from '../../services/authService';
import VentureLoader from '../../components/VentureLoader';

const RecentVenturePage = () => {
  const [sessions, setSessions] = useState<IRecentChats[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const hasFetched = useRef(false);

  useEffect(() => {
    if (hasFetched.current) return;
    hasFetched.current = true;
    
    async function loadSessions() {
      try {
        const data = await fetchSessions();
        setSessions(Array.isArray(data) ? data : [data]);
      } catch (err) {
        console.error('Failed to load ventures:', err);
      } finally {
        setLoading(false);
      }
    }
    loadSessions();
  }, []);

  const goToChat = (sessionId: string) => {
    navigate(`/ventures/${sessionId}`);
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return 'Recent';
    }
  };

  const getPhaseColor = (phase: string) => {
    console.log(phase);

    const phaseColors = {
      'KYC': 'bg-blue-100 text-blue-800',
      'BUSINESS_PLAN': 'bg-purple-100 text-purple-800',
      'execution': 'bg-green-100 text-green-800',
      'review': 'bg-orange-100 text-orange-800',
      'complete': 'bg-emerald-100 text-emerald-800'
    };
    return phaseColors[phase?.toLowerCase() as keyof typeof phaseColors] || 'bg-gray-100 text-gray-800';
  };

  const getProgressPercentage = (answeredCount: number, totalQuestions: number = 10) => {
    return Math.min((answeredCount / totalQuestions) * 100, 100);
  };

  return (
    <div className="min-h-screen bg-gradient-to-tr from-teal-50 to-blue-50 py-28 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-teal-500 to-blue-500 rounded-xl flex items-center justify-center">
              <span className="text-2xl">🚀</span>
            </div>
            <div>
              <h1 className="text-4xl font-bold text-teal-700">Your Ventures</h1>
              <p className="text-gray-600 mt-1">Continue building your entrepreneurial vision</p>
            </div>
          </div>
        </div>

        {loading ? (
          <VentureLoader title='Loading your ventures' />
        ) : sessions.length === 0 ? (
          <div className="text-center py-20">
            <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-4xl text-gray-400">💭</span>
            </div>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">No ventures yet</h2>
            <p className="text-gray-600 mb-8">Start your first business venture to see it here</p>
            <button
              onClick={() => navigate('/ventures/new-session')}
              className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white px-8 py-3 rounded-xl font-medium transition-colors"
            >
              Start New Venture
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sessions.map((sesh) => (
              <div
                key={sesh.id}
                className="bg-white rounded-2xl shadow-md hover:shadow-xl transition-all cursor-pointer border border-white/30 backdrop-blur-xl bg-white/70"
                onClick={() => goToChat(sesh.id)}
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold text-gray-900 mb-2 group-hover:text-teal-600 transition-colors">
                        {sesh.title || 'Untitled Venture'}
                      </h3>
                      <p className="text-sm text-gray-500">
                        {sesh.created_at ? formatDate(sesh.created_at) : 'Recent'}
                      </p>
                    </div>
                    <div className="flex items-center text-gray-400 group-hover:text-teal-600 transition-colors">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>

                  <div className="mb-4">
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${getPhaseColor(sesh.current_phase)}`}>
                      {sesh.current_phase || 'In Progress'}
                    </span>
                  </div>

                  <div className="mb-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700">Progress</span>
                      <span className="text-sm text-gray-500">{sesh.answered_count || 0} questions</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-teal-500 to-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${getProgressPercentage(sesh.answered_count || 0)}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
                <div className="px-6 py-4 bg-teal-50 border-t border-white/20 rounded-2xl">
                  <div className="flex items-center justify-end">
                    <div className="hidden items-center gap-2 text-sm text-gray-600">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>Last active</span>
                    </div>
                    <button className="text-teal-600 hover:text-teal-700 font-medium text-sm transition-colors">
                      Continue →
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {sessions.length > 0 && (
          <div className="text-center mt-12">
            <button
              onClick={() => navigate('/ventures/new-session')}
              className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white px-8 py-3 rounded-xl font-medium transition-all duration-300 shadow-lg hover:shadow-xl"
            >
              Start New Venture
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default RecentVenturePage;
