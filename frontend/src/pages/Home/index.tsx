import React, { useEffect } from 'react';
import { motion, useAnimation } from 'framer-motion';
import type { Variants } from 'framer-motion';
import { useInView } from 'react-intersection-observer';
import { Link } from 'react-router-dom';
import { FaBolt, FaUsers, FaChartBar } from 'react-icons/fa';

import businessPlanningImg from '../../assets/images/home/business-planning.jpg'
import launchRoadmapImg from '../../assets/images/home/launch-roadmap.jpg'
import implementationImg from '../../assets/images/home/implementation.jpg'
// import businessServiceNetworkImg from '../../assets/images/home/business-services-network.jpg'
// import saasProductImg from '../../assets/images/home/saas-product.jpg'
import avatar1Img from '../../assets/images/home/avatar-1.webp'
import avatar2Img from '../../assets/images/home/avatar-2.webp'
import avatar3Img from '../../assets/images/home/avatar-3.webp'


// Define MotionLink for animated Links
const MotionLink = motion(Link);

// Types
interface CardItem { title: string; text: string; image: string; }
interface Testimonial { name: string; role: string; quote: string; image: string; }

// Data
const angels: CardItem[] = [
  {
    title: 'Business Planning',
    text: 'Engage in an interactive, guided process that begins with helps you build a comprehensive business plan tailored to your business idea.',
    image: businessPlanningImg,
  },
  {
    title: 'Launch Roadmap',
    text: 'Once the business plan is complete, Angel will auto-generate a bespoke roadmap for you of milestones to complete so you can launch your business.',
    image: launchRoadmapImg,
  },
  {
    title: 'Implementation',
    text: 'Angel will then guide you through that roadmap, step by step, where each milestone is broken down into simplified and actionable tasks.',
    image: implementationImg,
  },
];

const features: CardItem[] = [
  {
    title: 'Guided Workflow',
    text: 'Angel walks you through every component of your business plan to help both you and Angel create a detailed business plan, providing guidance and research inputs along the way.',
    image: '',
  },
  {
    title: 'Task Automation',
    text: 'As Angel learns more about your business, it can complete tasks on your behalf to make the business startup process easier.',
    image: '',
  },
  {
    title: 'Domain Expertise',
    text: 'Angel is trained on deep subject matter so it can be an expert across regulatory and compliance, financial, marketing, business model and operations to provide accurate and bespoke guidance to help you navigate the business startup process.',
    image: '',
  },
];

// Only three icons to match three features
const featureIcons = [FaUsers, FaBolt, FaChartBar];

// const comingSoon: CardItem[] = [
//   {
//     title: 'SaaS Product Providers',
//     text: 'Founderport will onboard industry-leading products such as Intuit QuickBooks, LegalZoom, Airtable and other providers to further enhance entrepreneurs’ ability to automate and manage their businesses.',
//     image: saasProductImg,
//   },
//   {
//     title: 'Business Services Network',
//     text: 'We will provide a curated network of vetted service providers offering services such as legal, accounting, marketing, consulting and other services to help founders grow.',
//     image: businessServiceNetworkImg,
//   },
// ];

const testimonials: Testimonial[] = [
  {
    name: 'Oliver Bennett',
    role: 'Tech Startup CTO',
    quote: 'Angel has revolutionized how I balance work and well-being.',
    image: avatar1Img,
  },
  {
    name: 'James Clarke',
    role: 'CEO & Co-founder',
    quote: 'Staying productive without burning out has never been easier.',
    image: avatar2Img,
  },
  {
    name: 'Emma Hughes',
    role: 'Product Manager',
    quote: 'The community support feature is a game-changer for daily motivation.',
    image: avatar3Img,
  },
];

// Animation variants
const reveal: Variants = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0 },
};
const hoverCard: Variants = {
  hover: { scale: 1.04, boxShadow: '0 8px 24px rgba(0,0,0,0.12)' },
};

// Section wrapper
interface SectionProps { id?: string; bg?: string; title: string; children: React.ReactNode; }
const Section: React.FC<SectionProps> = ({ id, bg, title, children }) => {
  const controls = useAnimation();
  const [ref, inView] = useInView({ triggerOnce: true, threshold: 0.2 });
  useEffect(() => { if (inView) controls.start('visible'); }, [controls, inView]);

  return (
    <section id={id} className={`${bg ?? ''} py-16 px-4 lg:px-0`} ref={ref}>
      <motion.h2
        className="text-4xl lg:text-5xl font-extrabold text-gray-900 text-center mb-8 tracking-tight"
        initial="hidden"
        animate={controls}
        variants={reveal}
        transition={{ duration: 0.6 }}
      >
        {title}
      </motion.h2>
      <motion.div initial="hidden" animate={controls} variants={reveal} transition={{ delay: 0.2, duration: 0.6 }}>
        {children}
      </motion.div>
    </section>
  );
};

const FounderportHome: React.FC = () => {
  const heroControls = useAnimation();
  const [heroRef, heroInView] = useInView({ triggerOnce: true, threshold: 0.2 });
  useEffect(() => { if (heroInView) heroControls.start('visible'); }, [heroControls, heroInView]);

  return (
    <div className="relative overflow-hidden bg-gray-50 pt-32">
      {/* Hero Section */}
      <motion.section
        id="hero"
        ref={heroRef}
        className="relative py-20 px-4 lg:px-0 overflow-hidden"
        initial="hidden"
        animate={heroControls}
        variants={reveal}
        transition={{ duration: 0.6 }}
      >
        {/* SVG Accents */}
        <svg className="absolute -top-10 -left-10 w-64 h-64 opacity-20" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 200 200">
          <circle cx="100" cy="100" r="80" stroke="url(#grad1)" strokeWidth="20" />
          <defs>
            <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#14B8A6" />
              <stop offset="100%" stopColor="#0EA5E9" />
            </linearGradient>
          </defs>
        </svg>
        <svg className="absolute -bottom-10 -right-10 w-64 h-64 opacity-20" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 200 200">
          <rect x="20" y="20" width="160" height="160" stroke="url(#grad2)" strokeWidth="20" />
          <defs>
            <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#EC4899" />
              <stop offset="100%" stopColor="#8B5CF6" />
            </linearGradient>
          </defs>
        </svg>

        <motion.h2
          className="text-5xl lg:text-6xl font-extrabold text-gray-900 text-center mb-4 tracking-tight relative z-10"
          variants={reveal}
        >
          Welcome to Founderport
        </motion.h2>
        <motion.p
          className="text-xl text-gray-700 text-center max-w-2xl mx-auto mb-8 relative z-10"
          variants={reveal}
          transition={{ delay: 0.2 }}
        >
          Founderport is dedicated to simplifying the entrepreneurial journey for aspiring business owners.
        </motion.p>
        <motion.div
          className="flex justify-center space-x-4 relative z-10"
          variants={reveal}
          transition={{ delay: 0.4 }}
        >
          <MotionLink
            to="/login"
            className="px-6 py-3 bg-teal-600 text-white font-semibold rounded-full hover:bg-teal-700 transition"
            whileHover={{ scale: 1.05 }}
          >
            Get Started
          </MotionLink>
          <MotionLink
            to="/learn-more"
            className="px-6 py-3 border border-teal-600 text-teal-600 font-semibold rounded-full hover:bg-teal-50 transition"
            whileHover={{ scale: 1.05 }}
          >
            Learn More
          </MotionLink>
        </motion.div>
      </motion.section>

      {/* Angel Cards */}
      <Section id="angel" bg="bg-gradient-to-b from-white to-gray-100" title="Angel">
        <div className="grid gap-8 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto">
          {angels.map(item => (
            <motion.div
              key={item.title}
              className="bg-white rounded-2xl overflow-hidden"
              variants={hoverCard}
              whileHover="hover"
              transition={{ duration: 0.3 }}
            >
              <img src={item.image} alt={item.title} loading='lazy' className="w-full h-48 object-cover" />
              <div className="p-6">
                <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
                <p className="text-gray-600 text-sm">{item.text}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </Section>

      {/* Key Features with Icons + CTA */}
      <Section id="features" title="Key Features">
        <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto mb-8">
          {features.map((f, idx) => {
            const Icon = featureIcons[idx];
            return (
              <motion.div
                key={f.title}
                className="flex flex-col items-center p-6 bg-white rounded-xl shadow-sm text-center space-y-4"
                initial="hidden"
                animate="visible"
                variants={reveal}
                transition={{ delay: idx * 0.1, duration: 0.5 }}
              >
                <Icon size={40} className="text-teal-600" />
                <h4 className="font-medium text-gray-900">{f.title}</h4>
                <p className="text-gray-600 text-sm">{f.text}</p>
              </motion.div>
            );
          })}
        </div>
        <div className="text-center">
          <Link to="/features" className="px-6 py-2 bg-white text-teal-600 font-semibold rounded-full border border-teal-600 hover:bg-teal-50 transition mr-4">
            Learn More
          </Link>
          <Link to="/walkthrough" className="px-6 py-2 bg-teal-600 text-white font-semibold rounded-full hover:bg-teal-700 transition">
            Walkthrough
          </Link>
        </div>
      </Section>

      {/* Coming Soon with Alternating Layout */}
      {/* <Section id="coming" bg="bg-white" title="Coming Soon - Service Providers">
        <div className="space-y-12 max-w-6xl mx-auto">
          {comingSoon.map((c, i) => (
            <motion.div
              key={c.title}
              className={`flex flex-col ${i % 2 === 0 ? 'lg:flex-row' : 'lg:flex-row-reverse'} items-center gap-6`}
              initial="hidden"
              animate="visible"
              variants={reveal}
              transition={{ duration: 0.6 }}
            >
              <div className="flex-1">
                <h4 className="text-2xl font-semibold mb-2 text-gray-900">{c.title}</h4>
                <p className="text-gray-600 text-sm">{c.text}</p>
              </div>
              <img src={c.image} alt={c.title} loading='lazy' className="flex-1 w-full h-64 object-cover object-left-center rounded-xl shadow-md" />
            </motion.div>
          ))}
        </div>
      </Section> */}

      {/* Testimonials Improved */}
      <Section id="testimonials" bg="bg-gradient-to-b from-gray-100 to-white" title="What Our Founders Say">
        <div className="grid gap-8 grid-cols-1 md:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto">
          {testimonials.map((t, i) => (
            <motion.div
              key={t.name}
              className="bg-white rounded-2xl p-6 shadow-lg flex flex-col items-center text-center space-y-4"
              initial="hidden"
              animate="visible"
              variants={reveal}
              transition={{ delay: i * 0.2, duration: 0.5 }}
            >
              <img src={t.image} alt={t.name} loading='lazy' className="h-16 w-16 bg-gray-200 rounded-full flex items-center justify-center text-xl font-semibold text-gray-500" />
              <p className="italic text-gray-600">“{t.quote}”</p>
              <div className="font-semibold text-gray-900">{t.name}</div>
              <div className="text-gray-500 text-sm">{t.role}</div>
            </motion.div>
          ))}
        </div>
      </Section>
    </div>
  );
};

export default FounderportHome;
