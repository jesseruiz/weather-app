import { Routes, Route, NavLink, Navigate, useNavigate } from 'react-router';
import { Authenticator, useAuthenticator } from '@aws-amplify/ui-react';
import Home from './Home';
import Contact from './Contact';
import Dashboard from './Dashboard';
import UpdatePassword from './UpdatePassword';
import WeatherSliderWrapper from './WeatherSliderWrapper';
import ManageAlerts from './ManageAlerts';

import './amplify-configure';
import './App.css';

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

const myCards = [
  { id: 1, title: 'Card 1', description: 'This is the first card' },
  { id: 2, title: 'Card 2', description: 'This is the second card' },
  { id: 3, title: 'Card 3', description: 'This is the third card' },
  { id: 4, title: 'Card 4', description: 'This is the fourth card' },
  { id: 5, title: 'Card 5', description: 'This is the fifth card' },
];

// 🔐 Protected Route wrapper
function ProtectedRoute({ children }) {
  const { user } = useAuthenticator((context) => [context.user]);
  return user ? children : <Navigate to="/login" replace />;
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
          <li><NavLink to="/Contact">Contact</NavLink></li>
          {authStatus === 'authenticated' ? (
            <>
              <li><NavLink to="/dashboard">Account</NavLink></li>
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
          <Route path="/Dashboard" element={<Dashboard />} />
          <Route path="/Update-Password" element={<UpdatePassword />} />
          <Route path="/Manage-Alerts" element={<ManageAlerts />} />

          {/* Login page with Amplify UI */}
          <Route path="/login" element={
              <Authenticator formFields={formFields} loginMechanisms={['email']} signUpAttributes={['custom:City']}>
              {({ signOut, user }) => (
                <main>
                  <h1>Hello {user.name}</h1>
                  <button onClick={handleSignOut}>Sign out</button>
                </main>
              )}
            </Authenticator>
          } />
        </Routes>
      </main>

      <footer className="footer">
        <WeatherSliderWrapper />
      </footer>
    </div>
  );
}

  

export default App
