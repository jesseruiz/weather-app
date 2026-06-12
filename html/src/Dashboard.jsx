import { AccountSettings } from '@aws-amplify/ui-react';
import { useNavigate } from 'react-router';

export default function Dashboard() {
    const navigate = useNavigate();

    const handleSuccess = () => {
        alert('user has been successfully deleted')
        window.location.href = '/';
    }

    const handleClick = () => {
      navigate('/Update-Password');
    };

    const manageAlerts = () => {
        navigate('/Manage-Alerts');
    };

    return (
      <div className="dashboard">
        <h1 className="dashboard-header">Account Dashboard</h1>
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