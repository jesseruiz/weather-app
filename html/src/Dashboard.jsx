import { AccountSettings } from '@aws-amplify/ui-react';
import { useNavigate } from 'react-router';
import './Dashboard.css';

export default function Dashboard() {
    const navigate = useNavigate();

    const handleSuccess = () => {
        alert('Account has been successfully deleted');
        window.location.href = '/';
    };

    return (
      <div className="dashboard">
        <h1 className="dashboard-header">Account Dashboard</h1>

        <div className="dashboard-cards">
          <div className="dashboard-card">
            <h3 className="dashboard-card-title">Weather Alerts</h3>
            <p className="dashboard-card-desc">Configure email and SMS alerts for your saved city.</p>
            <button className="dashboard-btn" onClick={() => navigate('/Manage-Alerts')}>
              Manage Alerts
            </button>
          </div>

          <div className="dashboard-card">
            <h3 className="dashboard-card-title">Password</h3>
            <p className="dashboard-card-desc">Change your account password.</p>
            <button className="dashboard-btn" onClick={() => navigate('/Update-Password')}>
              Update Password
            </button>
          </div>

          <div className="dashboard-card dashboard-card-danger">
            <h3 className="dashboard-card-title">Delete Account</h3>
            <p className="dashboard-card-desc">Permanently remove your account and all associated data.</p>
            <AccountSettings.DeleteUser onSuccess={handleSuccess} />
          </div>
        </div>
      </div>
    );
}
