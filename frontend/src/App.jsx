import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import './styles/global.css';

import HomePage    from './pages/HomePage';
import AnalyzePage from './pages/AnalyzePage';
import EnhancePage from './pages/EnhancePage';
import ComparePage from './pages/ComparePage';

function Navbar() {
  const links = [
    { to: '/', label: 'Home', end: true },
    { to: '/analyze', label: 'Analyze' },
    { to: '/enhance', label: 'Enhance' },
    { to: '/compare', label: 'Compare' },
  ];
  return (
    <nav className="navbar">
      <div className="brand">
        <span style={{fontSize:'1.2rem'}}>⚡</span>
        <span>ResumeIQ</span>
      </div>
      <div className="nav-links">
        {links.map(({ to, label, end }) => (
          <NavLink key={to} to={to} end={end}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
            {label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/"        element={<HomePage />} />
        <Route path="/analyze" element={<AnalyzePage />} />
        <Route path="/enhance" element={<EnhancePage />} />
        <Route path="/compare" element={<ComparePage />} />
      </Routes>
      <Toaster position="top-right" toastOptions={{ duration: 3500 }} />
    </BrowserRouter>
  );
}
