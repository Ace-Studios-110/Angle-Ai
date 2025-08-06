import { useState, useEffect } from 'react';

const sections = [
  {
    title: "Empowerment & Support",
    icon: "💪",
    content:
      "We empower entrepreneurs by providing clear, actionable guidance at every step, ensuring they feel confident in building their business. Our system is built to simplify even the most complex processes, so users can focus on creating the business of their dreams. We use extensive research and proven best practices to provide recommendations that are both practical and inspiring.",
  },
  {
    title: "Bespoke & Dynamic",
    icon: "⚡",
    content:
      "Every piece of advice is tailored specifically to the user's individual needs, meaning that no two journeys are alike. Our system dynamically adjusts to inputs, ensuring that recommendations, resource links, and next steps are always contextually relevant. This bespoke approach guarantees that users receive differentiated support that aligns with their unique learning and building style.",
  },
  {
    title: "Unified Experience with Agentic Expertise",
    icon: "🤖",
    content:
      "Users interact solely with Angel, our single, cohesive interface, while behind the scenes, specialized agents provide deep, domain-specific guidance. These agents are trained using comprehensive, research-backed data sourced from credible government websites, industry reports, academic journals, and reputable news outlets. This integrated, hidden agent architecture ensures a seamless, consistent user experience with expert-level insights at every step.",
  },
  {
    title: "Action-Oriented Support",
    icon: "🎯",
    content:
      "We do as much as possible on behalf of the entrepreneur, actively guiding, drafting, and assisting in every step of the process. Our system is designed to take immediate actions—such as drafting emails, generating checklists, and analyzing proposals—to help reduce friction and accelerate progress. This proactive assistance ensures that the entrepreneur's journey is not only smooth but also highly efficient.",
  },
  {
    title: "Supportive Assistance",
    icon: "🤝",
    content:
      "We offer extra help when users encounter challenges by providing additional guidance and resources. Whether through dynamic prompts or tailored advice panels, we ensure that every user, regardless of experience level, feels supported and confident. Our language is friendly, respectful, and encouraging, making sure novice and experienced entrepreneurs alike feel valued and capable.",
  },
  {
    title: "Inclusive of All Experience Levels",
    icon: "🌟",
    content:
      "Our experience is designed with the assumption that most customers are first-time or novice entrepreneurs, yet it also accommodates seasoned business founders. We provide clear, step-by-step instructions while also offering deeper, strategic insights for those who need more advanced guidance. Our approach is kind, accommodating, and always geared toward building confidence, trust and promoting success.",
  },
];

export default function AboutUs() {
  const [activeSection, setActiveSection] = useState(0);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: { clientX: any; clientY: any; }) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-blue-50 to-indigo-50 relative overflow-hidden pt-20">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div 
          className="absolute w-96 h-96 bg-gradient-to-r from-teal-200/30 to-blue-200/30 rounded-full blur-3xl transition-transform duration-1000 ease-out"
          style={{
            transform: `translate(${mousePosition.x * 0.02}px, ${mousePosition.y * 0.02}px)`,
            left: '10%',
            top: '20%',
          }}
        />
        <div 
          className="absolute w-80 h-80 bg-gradient-to-r from-blue-200/20 to-indigo-200/20 rounded-full blur-3xl transition-transform duration-1000 ease-out"
          style={{
            transform: `translate(${mousePosition.x * -0.015}px, ${mousePosition.y * -0.015}px)`,
            right: '10%',
            bottom: '20%',
          }}
        />
      </div>

      <div className="relative z-10 py-20 px-4 md:px-8 lg:px-12">
        <div className="max-w-7xl mx-auto">
          {/* Hero Section */}
          <div className="text-center mb-20">
            <div className="inline-block bg-white/80 backdrop-blur-xl border border-white/40 rounded-full px-6 py-2 mb-6 shadow-lg">
              <span className="text-teal-600 font-medium text-sm">✨ Discover Our Story</span>
            </div>
            <h1 className="text-6xl md:text-7xl font-black bg-gradient-to-r from-teal-600 via-blue-600 to-indigo-600 bg-clip-text text-transparent mb-6 leading-tight">
              About Us
            </h1>
            <p className="text-xl md:text-2xl text-gray-600 max-w-4xl mx-auto leading-relaxed font-light">
              Empowering entrepreneurs with intelligent, personalized guidance to transform 
              <span className="font-semibold text-teal-600"> ideas into successful ventures</span>
            </p>
          </div>

          {/* Interactive Sections */}
          <div className="grid lg:grid-cols-2 gap-8 mb-20">
            {/* Navigation Pills */}
            <div className="space-y-4">
              <h3 className="text-2xl font-bold text-teal-700 mb-6">Our Core Values</h3>
              {sections.map((section, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-2xl cursor-pointer transition-all duration-300 ${
                    activeSection === index
                      ? 'bg-white/90 backdrop-blur-xl border border-white/50 shadow-xl scale-105'
                      : 'bg-white/60 backdrop-blur-md border border-white/30 hover:bg-white/70 hover:scale-102'
                  }`}
                  onClick={() => setActiveSection(index)}
                >
                  <div className="flex items-center space-x-4">
                    <div className={`text-3xl transition-transform duration-300 ${
                      activeSection === index ? 'scale-125' : ''
                    }`}>
                      {section.icon}
                    </div>
                    <div>
                      <h4 className={`font-bold transition-colors duration-200 ${
                        activeSection === index ? 'text-teal-700' : 'text-gray-700'
                      }`}>
                        {section.title}
                      </h4>
                      <div className={`h-1 bg-gradient-to-r from-teal-500 to-blue-500 rounded-full transition-all duration-300 ${
                        activeSection === index ? 'w-full mt-2' : 'w-0'
                      }`} />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Content Display */}
            <div className="bg-white/80 backdrop-blur-xl border border-white/40 rounded-3xl p-8 md:p-10 shadow-2xl sticky top-8">
              <div className="text-center mb-6">
                <div className="text-6xl mb-4 animate-bounce">
                  {sections[activeSection].icon}
                </div>
                <h2 className="text-3xl font-bold text-teal-700 mb-4">
                  {sections[activeSection].title}
                </h2>
              </div>
              <p className="text-gray-700 text-lg leading-relaxed">
                {sections[activeSection].content}
              </p>
            </div>
          </div>

          {/* Stats Section */}
          <div className="bg-white/70 backdrop-blur-xl border border-white/30 rounded-3xl p-8 md:p-12 shadow-2xl mb-20">
            <div className="grid md:grid-cols-3 gap-8 text-center">
              <div className="space-y-2">
                <div className="text-4xl md:text-5xl font-black bg-gradient-to-r from-teal-600 to-blue-600 bg-clip-text text-transparent">
                  10K+
                </div>
                <p className="text-gray-600 font-medium">Entrepreneurs Empowered</p>
              </div>
              <div className="space-y-2">
                <div className="text-4xl md:text-5xl font-black bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  95%
                </div>
                <p className="text-gray-600 font-medium">Success Rate</p>
              </div>
              <div className="space-y-2">
                <div className="text-4xl md:text-5xl font-black bg-gradient-to-r from-indigo-600 to-teal-600 bg-clip-text text-transparent">
                  24/7
                </div>
                <p className="text-gray-600 font-medium">AI Support Available</p>
              </div>
            </div>
          </div>

          {/* Call to Action */}
          <div className="text-center">
            <div className="bg-gradient-to-r from-teal-500 to-blue-500 rounded-3xl p-12 shadow-2xl relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-teal-600/20 to-blue-600/20 backdrop-blur-sm" />
              <div className="relative z-10">
                <h3 className="text-3xl md:text-4xl font-bold text-white mb-6">
                  Ready to Transform Your Vision?
                </h3>
                <p className="text-teal-100 text-xl mb-8 max-w-2xl mx-auto">
                  Join thousands of successful entrepreneurs who started their journey with us
                </p>
                <button className="bg-white text-teal-600 px-10 py-4 rounded-2xl font-bold text-lg hover:scale-105 hover:shadow-2xl transition-all duration-300 hover:bg-gray-50">
                  Start Your Journey Today →
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}