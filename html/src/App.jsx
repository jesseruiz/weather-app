import { Routes, Route, NavLink, Navigate, useNavigate } from 'react-router';
import { useEffect } from 'react';
import { Authenticator, useAuthenticator } from '@aws-amplify/ui-react';
import Home from './Home';
import Contact from './Contact';
import Dashboard from './Dashboard';
import UpdatePassword from './UpdatePassword';
import ManageAlerts from './ManageAlerts';
import './amplify-configure';
import './App.css';
import MyForecastWrapper from './MyForecastWrapper';

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
    return <div style={{ textAlign: 'center', marginTop: '50px' }}>Loading session...</div>;
  }

  // Once it finishes configuring, decide whether to show the page or kick them to login
  return user ? children : <Navigate to="/login" replace />;
}

// 🛠️ LoginRedirect: Moved outside of the App component to prevent memory leaks and infinite loops
function LoginRedirect() {
  const navigate = useNavigate();
  
  useEffect(() => {
    navigate('/');
  }, [navigate]);
  
  return null;
}

function App() {

  const { authStatus, user, signOut } = useAuthenticator((ctx) => [ctx.authStatus, ctx.user]);
  const navigate = useNavigate();

  const handleSignOut = async () => {
    await signOut();
    // THE FIX: Forces a hard browser refresh to wipe Amplify's stale global state!
    window.location.href = '/'; 
  };
  
  return (
    <div className="app">
      <nav>
        <ul>
          <li className='logo'><NavLink to="/">Rain for thee</NavLink></li>
          <li><NavLink to="/">Home</NavLink></li>
          {authStatus === 'authenticated' ? (
            <>
              <li><NavLink to="/MyForecast">My Forecast</NavLink></li>
              <li><NavLink to="/Dashboard">Account</NavLink></li>
              <li><button onClick={handleSignOut}>Sign Out</button></li>
            </>
          ) : (
            <li><NavLink to="/login">Login</NavLink></li>
          )}
        </ul>
      </nav>

      <main>
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

          {/* Login page with Amplify UI */}
          <Route path="/login" element={
              <Authenticator formFields={formFields} loginMechanisms={['email']} signUpAttributes={['custom:City']}>
              {({ signOut, user }) => (
                <LoginRedirect />
              )}
            </Authenticator>
          } />
        </Routes>
      </main>

      <footer className="footer">
      </footer>
    </div>
  );
}

export default App;