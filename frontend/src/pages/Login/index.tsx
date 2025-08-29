import React, { useState } from 'react';
import { FaEye, FaEyeSlash, FaEnvelope, FaLock, FaArrowRight, FaMagic } from 'react-icons/fa';
import { Link } from 'react-router-dom';
import { setSession } from '../../utils/tokenUtils';
import { toast } from 'react-toastify';
import { signIn } from '../../api/authService';

interface LoginFormData {
  email: string;
  password: string;
}

const LoginPage: React.FC = () => {
  const [formData, setFormData] = useState<LoginFormData>({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };
// 
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    if (!formData.email || !formData.password) {
      toast.warn('Please fill in all required fields');
      return;
    }
    if (!/\S+@\S+\.\S+/.test(formData.email)) {
      toast.warn('Please enter a valid email address');
      return;
    }
    try {
      const session = await signIn(formData);
      setSession(session.access_token, session.refresh_token);
      setTimeout(() => {
        window.location.href = '/ventures';
      }, 1000);
    } catch (err: any) {
      console.log('Signin error:', err.message);
      toast.error(
        err.message || 'Signup failed. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-gray-50">
      {/* Soft Teal Background Glows */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-teal-600/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-teal-400/5 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      <div className="relative z-10 flex items-center justify-center min-h-screen p-4">
        <div className="w-full max-w-md">
          {/* Frosted Glass Card */}
          <div className="backdrop-blur-xl bg-white/80 rounded-3xl border border-teal-200 shadow-lg overflow-hidden hover:scale-[1.02] transition-transform duration-300">
            {/* Header with Teal Accent */}
            <div className="relative p-8 pb-6">
              <div className="absolute inset-0 bg-gradient-to-r from-teal-400 to-teal-600"></div>
              <div className="relative text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-teal-600 to-teal-600 rounded-2xl mb-6 shadow-md">
                  <FaMagic className="w-8 h-8 text-white" />
                </div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome Back</h1>
                <p className="text-gray-700">Sign in to continue your journey</p>
              </div>
            </div>

            {/* Form Fields */}
            <form className="p-8 pt-2" onSubmit={handleSubmit}>
              <div className="space-y-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">Email Address</label>
                  <div className="relative">
                    <FaEnvelope className={`absolute left-3 top-3 text-gray-400`} />
                    <input
                      id="email"
                      name="email"
                      type="email"
                      required
                      autoComplete="email"
                      value={formData.email}
                      onChange={handleChange}
                      placeholder="Enter your email"
                      className="w-full pl-12 pr-4 py-3 bg-white border border-gray-200 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:border-teal-600 transition"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">Password</label>
                  <div className="relative">
                    <FaLock className="absolute left-3 top-3 text-gray-400" />
                    <input
                      id="password"
                      name="password"
                      type={showPassword ? 'text' : 'password'}
                      required
                      autoComplete="current-password"
                      value={formData.password}
                      onChange={handleChange}
                      placeholder="Enter your password"
                      className="w-full pl-12 pr-12 py-3 bg-white border border-gray-200 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:border-teal-600 transition"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 transition"
                    >
                      {showPassword ? <FaEyeSlash /> : <FaEye />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full flex items-center justify-center py-3 bg-gradient-to-r from-teal-500 to-teal-600 text-white font-semibold rounded-lg hover:from-teal-600 hover:to-teal-700 transition"
                >
                  {isLoading ? 'Signing in...' : <>Sign In <FaArrowRight className="ml-2" /></>}
                </button>

                <div className="text-center">
                  <p className="text-gray-600">
                    Don’t have an account? <Link to="/signup" className="text-teal-600 hover:underline">Sign up now</Link>
                  </p>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;