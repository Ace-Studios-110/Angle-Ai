import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { FaTwitter, FaLinkedin, FaGithub, FaInstagram } from 'react-icons/fa';
import LOGO from '../../assets/images/home/Founderport_Logo_Horizontal_Mariner_Main.svg';

const socialLinks = [
  { icon: FaTwitter, href: 'https://twitter.com/founderport', label: 'Twitter' },
  { icon: FaLinkedin, href: 'https://linkedin.com/company/founderport', label: 'LinkedIn' },
  { icon: FaGithub, href: 'https://github.com/founderport', label: 'GitHub' },
  { icon: FaInstagram, href: 'https://instagram.com/founderport', label: 'Instagram' },
];

const footerLinks = {
  Businesses: ['Startups', 'Enterprise', 'Case Studies', 'Partners'],
  Resources: ['Blog', 'Documentation', 'Guides', 'Support'],
};

const Footer: React.FC = () => (
  <footer className="relative bg-gradient-to-tr from-teal-50 to-blue-50 pt-12 pb-8 px-4 sm:px-6 lg:px-8">
    {/* Decorative Blobs */}
    <div className="absolute -top-20 left-0 w-64 h-64 bg-gradient-to-br from-teal-300 to-blue-400 opacity-20 rounded-full filter blur-3xl animate-blob"></div>

    <div className="relative max-w-7xl mx-auto z-10">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* Column 1: Brand + Social */}
        <div className="space-y-4">
          <Link to="/" className="text-2xl font-bold text-teal-600 transition-colors">
            <img
              src={LOGO}
              alt="Founderport Logo"
              className={`transition-all duration-300 h-20 w-auto`}
            />
          </Link>
          <p className="text-gray-600">Building the future of business infrastructure.</p>
          <div className="flex space-x-4">
            {socialLinks.map(({ icon: Icon, href, label }) => (
              <motion.a
                key={label}
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={label}
                className="text-gray-600 hover:text-teal-600 transition-colors"
                whileHover={{ scale: 1.1 }}
              >
                <Icon size={20} />
              </motion.a>
            ))}
          </div>
        </div>

        {/* Spacer */}
        <div className="hidden md:block"></div>

        {/* Links Columns */}
        {Object.entries(footerLinks).map(([section, items]) => (
          <div key={section} className="space-y-4">
            <h3 className="text-lg font-semibold text-teal-600">{section}</h3>
            <ul className="space-y-2">
              {items.map(item => {
                const MotionLink = motion(Link);
                return (
                  <li key={item}>
                    <MotionLink
                      to={`/${item.toLowerCase().replace(/\s+/g, '-')}`}
                      className="text-gray-600 hover:text-teal-600 transition-colors block"
                      whileHover={{ x: 5 }}
                    >
                      {item}
                    </MotionLink>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>

      {/* Copyright */}
      <div className="border-t border-gray-200 mt-8 pt-6 text-sm text-gray-500 text-center md:text-left">
        © {new Date().getFullYear()} Founderport LLC. All rights reserved.
      </div>
    </div>
  </footer>
);

export default Footer;