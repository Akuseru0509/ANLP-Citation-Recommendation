import React from 'react';
import { BrowserRouter, Link, useLocation } from 'react-router-dom';
import AppRoutes from './routes';
import './App.css';

function NavBar() {
  const location = useLocation();

  return (
    <nav className="navbar" id="navbar">
      <div className="navbar-brand">
        <span className="navbar-logo">📑</span>
        <span className="navbar-title">CiteRec</span>
      </div>
      <div className="navbar-links">
        <Link to="/" className={`nav-link${location.pathname === '/' ? ' active' : ''}`}>Home</Link>
        <Link to="/chatbot" className={`nav-link${location.pathname === '/chatbot' ? ' active' : ''}`}>Chatbot</Link>
      </div>
    </nav>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="App">
        <NavBar />

        <AppRoutes />
      </div>
    </BrowserRouter>
  );
}

export default App;
