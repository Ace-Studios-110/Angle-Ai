import { useLocation, useNavigate } from 'react-router-dom';
import { FaEnvelopeOpenText } from 'react-icons/fa';

const VerifyEmailPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const email = location.state?.email;

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
            <div className="max-w-md w-full text-center bg-white rounded-3xl p-8 shadow-md border border-gray-100">
                <div className="flex justify-center mb-4">
                    <div className="bg-teal-100 text-teal-600 rounded-full p-4">
                        <FaEnvelopeOpenText className="text-4xl" />
                    </div>
                </div>
                <h1 className="text-2xl font-bold text-gray-800 mb-2">Check your email</h1>
                <p className="text-gray-600">
                    We’ve sent a verification link to <span className="font-medium">{email || 'your email'}</span>.
                </p>
                <p className="text-sm text-gray-500 mt-2">
                    Please verify your email to continue using your account.
                </p>

                <button
                    onClick={() => navigate('/login')}
                    className="mt-6 w-full bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-600 hover:to-teal-700 text-white py-2 rounded-lg transition"
                >
                    Go to Login
                </button>
            </div>
        </div>
    );
};

export default VerifyEmailPage;
