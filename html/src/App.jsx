import { Routes, Route, NavLink, Navigate, useNavigate } from 'react-router';
import { useEffect } from 'react';
import { Authenticator, useAuthenticator } from '@aws-amplify/ui-react';
import Home from './Home';
import Contact from './Contact';
import Dashboard from './Dashboard';
import UpdatePassword from './UpdatePassword';
import WeatherSliderWrapper from './WeatherSliderWrapper';
import ManageAlerts from './ManageAlerts';
import MyForecast from './MyForecast'

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

// 🔐 Protected Route wrapper
function ProtectedRoute({ children }) {
  const { user } = useAuthenticator((context) => [context.user]);
  return user ? children : <Navigate to="/login" replace />;
}

// 🛠️ THE FIX: Moved outside of the App component to prevent memory leaks and infinite loops
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
    navigate('/'); // Redirect to home after sign out
  };
  
  return (
    <div className="app">
      <nav>
        <ul>
          <li className='logo'><NavLink to="/">On A Heater!</NavLink></li>
          <li><NavLink to="/">Home</NavLink></li>
          <li><a href="https://buy.stripe.com/test_00w3cx64Gbirdf5cSzgUM00" target="_blank" rel="noopener noreferrer">
              Donate
              </a>
          </li>
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
       {/*<WeatherSliderWrapper /> */}
      </footer>
    </div>
  );
}

export default App;