import React from 'react';

interface ServiceProvider {
  name: string;
  type: string;
  description: string;
  pricing: string;
  local: boolean;
  website: string;
  rating: number;
  specialties: string[];
}

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

interface ServiceProviderModalProps {
  isOpen: boolean;
  onClose: () => void;
  providers: ServiceProvider[];
  task: ImplementationTask | null;
}

const ServiceProviderModal: React.FC<ServiceProviderModalProps> = ({
  isOpen,
  onClose,
  providers,
  task
}) => {
  if (!isOpen || !task) return null;

  const handleContactProvider = (provider: ServiceProvider) => {
    // Open provider website in new tab
    if (provider.website && provider.website.startsWith('http')) {
      window.open(provider.website, '_blank');
    } else {
      // Copy contact info to clipboard
      const contactInfo = `${provider.name}\n${provider.type}\n${provider.description}\nPricing: ${provider.pricing}\nWebsite: ${provider.website}`;
      navigator.clipboard.writeText(contactInfo);
      alert('Contact information copied to clipboard!');
    }
  };

  const getRatingStars = (rating: number) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;

    for (let i = 0; i < fullStars; i++) {
      stars.push('★');
    }
    if (hasHalfStar) {
      stars.push('☆');
    }
    const emptyStars = 5 - Math.ceil(rating);
    for (let i = 0; i < emptyStars; i++) {
      stars.push('☆');
    }

    return stars.join('');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-500 to-blue-500 p-6 text-white rounded-t-xl">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">Service Providers</h2>
              <p className="text-purple-100 mt-1">Recommended providers for {task.title}</p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-purple-200 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Task Context */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h3 className="font-semibold text-gray-900 mb-2">Task Context</h3>
            <p className="text-gray-700 text-sm mb-2">{task.description}</p>
            <div className="text-xs text-gray-500">
              <span className="font-medium">Business:</span> {task.business_context.business_name} • 
              <span className="font-medium ml-1">Industry:</span> {task.business_context.industry} • 
              <span className="font-medium ml-1">Location:</span> {task.business_context.location}
            </div>
          </div>

          {/* Providers List */}
          <div className="space-y-4">
            {providers.map((provider, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-semibold text-gray-900">{provider.name}</h3>
                      {provider.local && (
                        <span className="bg-green-100 text-green-800 text-xs font-medium px-2 py-1 rounded-full">
                          (Local)
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{provider.type}</p>
                    <p className="text-gray-700 mb-3">{provider.description}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-semibold text-gray-900">{provider.pricing}</div>
                    <div className="text-sm text-gray-600">Starting price</div>
                  </div>
                </div>

                {/* Rating */}
                <div className="flex items-center gap-2 mb-3">
                  <div className="text-yellow-500 text-lg">
                    {getRatingStars(provider.rating)}
                  </div>
                  <span className="text-sm text-gray-600">
                    {provider.rating}/5 rating
                  </span>
                </div>

                {/* Specialties */}
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Specialties:</h4>
                  <div className="flex flex-wrap gap-2">
                    {provider.specialties.map((specialty, specIndex) => (
                      <span
                        key={specIndex}
                        className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full"
                      >
                        {specialty}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Contact Button */}
                <div className="flex justify-end">
                  <button
                    onClick={() => handleContactProvider(provider)}
                    className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
                  >
                    <span>📞</span>
                    Contact Provider
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Additional Resources */}
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900 mb-2">💡 Additional Resources</h3>
            <div className="text-sm text-blue-800 space-y-1">
              <p>• Research each provider thoroughly before making a decision</p>
              <p>• Ask for references and case studies relevant to your industry</p>
              <p>• Compare pricing and services across multiple providers</p>
              <p>• Consider local providers for personalized service and support</p>
              <p>• Check reviews and ratings on independent platforms</p>
            </div>
          </div>

          {/* Angel Assistance */}
          <div className="mt-6 bg-teal-50 border border-teal-200 rounded-lg p-4">
            <h3 className="font-semibold text-teal-900 mb-2">✨ How Angel Can Help</h3>
            <div className="text-sm text-teal-800 space-y-1">
              <p>• Draft initial outreach emails to providers</p>
              <p>• Create comparison matrices for decision-making</p>
              <p>• Generate questions to ask during provider interviews</p>
              <p>• Review and analyze provider proposals</p>
              <p>• Help negotiate terms and pricing</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 rounded-b-xl flex justify-end">
          <button
            onClick={onClose}
            className="bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-lg font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default ServiceProviderModal;
