import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createSessions } from '../../services/authService';

const ideaPool = [
  'Remote Mental Wellness Platform',
  'AI-Powered Resume Coach',
  'Freelancer Tax Helper',
  'Virtual Interior Designer',
  'Pet Nutrition Tracker',
  'AI Co-founder Generator',
  'Startup Naming Assistant',
  'Local Farmer Market Finder',
  'Green Habit Tracker',
  'AI-Powered Business Plan Writer',
  'Voice Note to Blog Converter',
  'Remote Team Culture Platform',
  'Online Skill Bartering App',
  'Personal Productivity AI',
  'Health Insurance Explainer',
  'Niche Job Board for Creators',
  'Startup Pitch Validator',
  'Parenting Support AI',
  'Language Buddy Matcher',
  'Remote Dev Hiring Board'
];

const NewVenture = () => {
  const [title, setTitle] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [remainingIdeas, setRemainingIdeas] = useState([...ideaPool]);
  const navigate = useNavigate();

  const handleCreateVenture = async () => {
    if (!title.trim()) return;

    setStatus('loading');
    setErrorMessage(null);

    try {
      const venture = await createSessions(title);
      setStatus('success');

      setTimeout(() => {
        navigate(`/ventures/${venture.id}`);
      }, 1000);
    } catch (err) {
      setErrorMessage((err as Error).message || 'Could not create venture.');
      setStatus('error');
    }
  };

  const handleTryIdea = () => {
    if (remainingIdeas.length === 0) return;

    const randomIndex = Math.floor(Math.random() * remainingIdeas.length);
    const newIdea = remainingIdeas[randomIndex];

    setTitle(newIdea);
    setRemainingIdeas(remainingIdeas.filter((_, idx) => idx !== randomIndex));
  };

  return (
    <div className="min-h-screen bg-gradient-to-tr from-teal-50 to-blue-50 flex items-center justify-center px-4">
      <div className="w-full max-w-lg bg-white/70 backdrop-blur-xl border border-white/30 shadow-xl rounded-3xl p-8">
        <h1 className="text-3xl font-bold text-teal-700 text-center mb-2">Start a New Venture</h1>
        <p className="text-center text-gray-600 mb-6">Give your new business a name to get started.</p>

        <input
          type="text"
          placeholder="e.g. AI-Powered Tutor for Students"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          disabled={status === 'loading'}
          className="w-full px-4 py-3 rounded-xl border border-teal-100 focus:ring-2 focus:ring-teal-400 focus:outline-none transition"
        />

        {status === 'success' && (
          <div className="text-green-700 bg-green-50 border-l-4 border-green-500 p-3 mt-4 rounded-md text-sm">
            Venture created successfully!
          </div>
        )}

        {status === 'error' && errorMessage && (
          <div className="text-red-700 bg-red-50 border-l-4 border-red-500 p-3 mt-4 rounded-md text-sm">
            {errorMessage}
          </div>
        )}

        <button
          onClick={handleCreateVenture}
          disabled={status === 'loading' || !title.trim()}
          className={`w-full mt-6 py-3 rounded-xl font-medium transition-all ${status === 'loading' || !title.trim()
              ? 'bg-gray-300 cursor-not-allowed'
              : 'bg-gradient-to-r from-teal-500 to-blue-500 text-white hover:from-teal-600 hover:to-blue-600'
            }`}
        >
          {status === 'loading' ? 'Creating...' : 'Start New Venture'}
        </button>

        <p className="mt-6 text-sm text-center text-gray-500">
          Need inspiration?{' '}
          <span
            className={`text-teal-600 hover:underline cursor-pointer ${remainingIdeas.length === 0 ? 'opacity-50 cursor-not-allowed' : ''}`}
            onClick={handleTryIdea}
          >
            {remainingIdeas.length > 0 ? 'Try this idea' : 'No more ideas'}
          </span>
        </p>
      </div>
    </div>
  );
};

export default NewVenture;
