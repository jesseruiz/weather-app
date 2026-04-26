import { useAuthenticator } from '@aws-amplify/ui-react';
import { AccountSettings } from '@aws-amplify/ui-react';
import { useNavigate } from 'react-router';
import { useState } from 'react';

/* 
Need to update account deletion to redirect to home
*/

export default function Dashboard() {
    const { authStatus, user } = useAuthenticator((authState) => [authState.authStatus, authState.user]);
    const navigate = useNavigate();

    const handleSuccess = () => {
        alert('user has been successfully deleted')
        navigate('/')
    }

    const handleClick = () => {
      navigate('/Update-Password'); // Navigate to the dashboard page
    };

    const manageAlerts = () => {
        navigate('/Manage-Alerts');
    };

    return (
      <div className="dashboard">
        <h1 className="dashboard-header">Account Dashboard</h1>
        <div>
            <h3>Update Email</h3>
        </div>
        <div>
            <h3>Manage Weather Alerts</h3>
            <button onClick={manageAlerts}>Manage Alerts</button>
        </div>
        <div>
            <h3>Update Password</h3>
            <button onClick={handleClick}>Update Password?</button>
        </div>
        <div>
            <h3>Delete Account</h3>
            <AccountSettings.DeleteUser onSuccess={handleSuccess} />
        </div>
      </div>
    );
  }