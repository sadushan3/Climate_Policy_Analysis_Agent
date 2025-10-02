import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function Navbar() {
  const location = useLocation();

  const NavLink = ({ to, children }) => {
    const isActive = location.pathname === to;
    return (
      <Link
        to={to}
        className={`px-4 py-2 rounded-lg transition ${
          isActive
            ? 'text-indigo-600 font-semibold bg-indigo-50'
            : 'text-gray-600 hover:text-indigo-600 hover:bg-gray-50'
        }`}
      >
        {children}
      </Link>
    );
  };

  return (
    <nav className="bg-white shadow-sm">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-2">
            <svg
              className="w-8 h-8 text-indigo-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
              />
            </svg>
            <span className="text-xl font-bold text-gray-800">
              Climate Policy Analysis
            </span>
          </div>

          <div className="flex space-x-4">
            <NavLink to="/">Compare</NavLink>
            <NavLink to="/upload">Upload</NavLink>
            <NavLink to="/analysis">Analysis</NavLink>
            <a
              href="https://github.com/sadushan3/Climate_Policy_Analysis_Agent"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-600 hover:text-indigo-600 px-4 py-2 rounded-lg transition hover:bg-gray-50"
            >
              GitHub
            </a>
          </div>
        </div>
      </div>
    </nav>
  );
}