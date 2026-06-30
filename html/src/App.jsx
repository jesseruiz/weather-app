import { Routes, Route, NavLink, Navigate, useNavigate, useLocation } from 'react-router';
import { useEffect, useState } from 'react';
import { Authenticator, useAuthenticator } from '@aws-amplify/ui-react';
import { signOut as amplifySignOut } from 'aws-amplify/auth';
import Home from './Home';
import Contact from './Contact';
import Dashboard from './Dashboard';
import UpdatePassword from './UpdatePassword';
import ManageAlerts from './ManageAlerts';
import './amplify-configure';
import './App.css';
import MyForecastWrapper from './MyForecastWrapper';
import Trivia from './Trivia';

const formFields = {
  signUp: {
    name: {
      order: 1
    },
    email: {
      order: 2
    },
    'custom:City': {
      order: 3,
      placeholder: 'City',
      isRequired: true,
      label: 'City'
    },
    password: {
      order: 4
    },
    confirm_password: {
      order: 5
    }
  },
 }

// 🔐 Protected Route wrapper that waits for Amplify to finish configuring
function ProtectedRoute({ children }) {
  const { authStatus, user } = useAuthenticator((context) => [context.authStatus, context.user]);

  // If Amplify is still checking local storage, show a loading state
  if (authStatus === 'configuring') {
    return <div className="loading-session">Loading session...</div>;
  }

  // Once it finishes configuring, decide whether to show the page or kick them to login
  return user ? children : <Navigate to="/login" replace />;
}

function LoginRedirect() {
  const navigate = useNavigate();
  useEffect(() => { navigate('/'); }, [navigate]);
  return null;
}

function LoginPage() {
  return (
    <div className="login-page">
      <div className="login-branding">
        <h1>Rain for Thee</h1>
        <p>Weather forecasts and alerts for your city</p>
      </div>
      <Authenticator formFields={formFields} loginMechanisms={['email']} signUpAttributes={['custom:City']}>
        {() => <LoginRedirect />}
      </Authenticator>
    </div>
  );
}

const PAGE_TITLES = {
  '/':               'Home | Rain for Thee',
  '/Trivia':         'Daily Trivia | Rain for Thee',
  '/MyForecast':     'My Forecast | Rain for Thee',
  '/Dashboard':      'Account | Rain for Thee',
  '/Manage-Alerts':  'Manage Alerts | Rain for Thee',
  '/Update-Password':'Update Password | Rain for Thee',
  '/Contact':        'Contact | Rain for Thee',
  '/login':          'Sign In | Rain for Thee',
};

function App() {
  const { authStatus } = useAuthenticator((ctx) => [ctx.authStatus, ctx.user]);
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    document.title = PAGE_TITLES[location.pathname] || 'Rain for Thee';
  }, [location.pathname]);

  const handleSignOut = async () => {
    await amplifySignOut();
    window.location.href = '/';
  };

  const closeMenu = () => setMenuOpen(false);

  useEffect(() => {
    if (!menuOpen) return;
    function handleOutside(e) {
      if (!e.target.closest('nav')) setMenuOpen(false);
    }
    document.addEventListener('click', handleOutside);
    return () => document.removeEventListener('click', handleOutside);
  }, [menuOpen]);

  return (
    <div className="app">
      <a href="#main-content" className="skip-link">Skip to main content</a>
      <nav>
        <div className="nav-bar">
          <NavLink to="/" className="nav-logo" onClick={closeMenu}>Rain for Thee</NavLink>
          <button
            className="hamburger"
            onClick={() => setMenuOpen(m => !m)}
            aria-label="Toggle navigation"
            aria-expanded={menuOpen}
          >
            {menuOpen ? '✕' : '☰'}
          </button>
          <ul className={`nav-links${menuOpen ? ' open' : ''}`}>
            <li><NavLink to="/" onClick={closeMenu}>Home</NavLink></li>
            <li><NavLink to="/Trivia" onClick={closeMenu}>Trivia</NavLink></li>
            {authStatus === 'authenticated' ? (
              <>
                <li><NavLink to="/MyForecast" onClick={closeMenu}>My Forecast</NavLink></li>
                <li><NavLink to="/Dashboard" onClick={closeMenu}>Account</NavLink></li>
                <li><button onClick={handleSignOut}>Sign Out</button></li>
              </>
            ) : (
              <li><NavLink to="/login" onClick={closeMenu}>Login</NavLink></li>
            )}
          </ul>
        </div>
      </nav>

      <main id="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/Contact" element={<Contact />} />
          <Route path="/Dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/Update-Password" element={
            <ProtectedRoute>
              <UpdatePassword />
            </ProtectedRoute>
          } />
          <Route path="/Manage-Alerts" element={
            <ProtectedRoute>
              <ManageAlerts />
            </ProtectedRoute>
          } />
          <Route path="/MyForecast" element={
            <ProtectedRoute>
              <MyForecastWrapper />
            </ProtectedRoute>
          } />
          <Route path="/Trivia" element={<Trivia />} />

          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </main>

      <footer className="footer">
      </footer>
    </div>
  );
}

export default App;