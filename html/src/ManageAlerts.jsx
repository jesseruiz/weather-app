import { useState, useEffect } from 'react';
import { useAuthenticator } from '@aws-amplify/ui-react';
import { fetchAuthSession } from 'aws-amplify/auth';
import { API_BASE } from './api';
import './ManageAlerts.css';

export default function ManageAlerts() {
  const { user } = useAuthenticator((context) => [context.user]);

  const [settings, setSettings] = useState({
    city: '',
    alertsEnabled: false,
    emailEnable: false,
    smsEnable: false,
    phoneNumber: '',
    alertFrequency: 'Any Change'
  });

  const [originalSettings, setOriginalSettings] = useState(null);
  const [status, setStatus] = useState({ loading: true, error: null, message: null });

  useEffect(() => {
    if (!user?.username) return;

    async function fetchSettings() {
      try {
        const session = await fetchAuthSession();
        const token = session.tokens?.idToken?.toString();

        if (!token) throw new Error("No valid auth token found.");

        const res = await fetch(`${API_BASE}/get_user?id=${user.username}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!res.ok) throw new Error('Failed to fetch settings');

        const data = await res.json();

        const fetchedSettings = {
          city: data.city || '',
          alertsEnabled: data.alertsEnabled || false,
          emailEnable: data.emailEnable || false,
          smsEnable: data.smsEnable || false,
          phoneNumber: data.phoneNumber || '',
          alertFrequency: data.alertFrequency || 'Any Change'
        };

        setSettings(fetchedSettings);
        setOriginalSettings(fetchedSettings);
        setStatus({ loading: false, error: null, message: null });

      } catch (err) {
        setStatus({ loading: false, error: err?.message || String(err), message: null });
      }
    }

    fetchSettings();
  }, [user?.username]);

  const hasChanges = originalSettings &&
    JSON.stringify(settings) !== JSON.stringify(originalSettings);

  const updateSetting = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    if (status.message) setStatus(prev => ({ ...prev, message: null }));
  };

  const handleSave = async () => {
    setStatus({ loading: true, error: null, message: null });

    const cityRegex = /^[A-Za-z\s.'-]+$/;
    if (settings.city && !cityRegex.test(settings.city)) {
      setStatus({ loading: false, error: 'City name can only contain letters, spaces, hyphens, and apostrophes.', message: null });
      return;
    }

    if (settings.smsEnable) {
      if (!settings.phoneNumber.trim()) {
        setStatus({ loading: false, error: 'A phone number is required to receive text alerts.', message: null });
        return;
      }
      const phoneRegex = /^\+[1-9]\d{9,14}$/;
      if (!phoneRegex.test(settings.phoneNumber.trim())) {
        setStatus({ loading: false, error: 'Phone number must be in E.164 format (e.g. +12065551234).', message: null });
        return;
      }
    }

    try {
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();

      if (!token) throw new Error("No valid auth token found.");

      const response = await fetch(`${API_BASE}/update_user`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(settings)
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error || 'Failed to save settings.');
      }

      const responseData = await response.json();

      const updatedSettings = {
        ...settings,
        city: responseData.city !== "Unchanged" ? responseData.city : settings.city
      };

      setSettings(updatedSettings);
      setOriginalSettings(updatedSettings);
      setStatus({ loading: false, error: null, message: 'Settings saved successfully!' });

    } catch (err) {
      setStatus({ loading: false, error: err.message, message: null });
    }
  };

  const handleCancel = () => {
    setSettings(originalSettings);
    setStatus({ ...status, error: null, message: null });
  };

  if (status.loading && !originalSettings) {
    return <div className="manage-alerts"><p>Loading settings...</p></div>;
  }

  return (
    <div className="manage-alerts">
      <h2>Manage Weather Alerts</h2>

      {status.error && <p className="status-error">{status.error}</p>}
      {status.message && <p className="status-success">{status.message}</p>}

      <div className="settings-form">

        <div>
          <label className="field-label">Tracked City:</label>
          <input
            type="text"
            placeholder="e.g., Seattle"
            value={settings.city}
            onChange={(e) => updateSetting('city', e.target.value)}
          />
        </div>

        <hr />

        <div>
          <label className="alerts-master-label">
            <input
              type="checkbox"
              checked={settings.alertsEnabled}
              onChange={(e) => updateSetting('alertsEnabled', e.target.checked)}
            />
            Enable Weather Alerts
          </label>
        </div>

        {settings.alertsEnabled && (
          <div className="alerts-nested">

            <div>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={settings.emailEnable}
                  onChange={(e) => updateSetting('emailEnable', e.target.checked)}
                />
                Receive Email Alerts
              </label>
            </div>

            <div>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={settings.smsEnable}
                  onChange={(e) => updateSetting('smsEnable', e.target.checked)}
                />
                Receive Text Messages
              </label>
            </div>

            {settings.smsEnable && (
              <div className="phone-field">
                <label className="phone-label">Phone Number:</label>
                <input
                  type="tel"
                  placeholder="+1234567890"
                  value={settings.phoneNumber}
                  onChange={(e) => updateSetting('phoneNumber', e.target.value)}
                />
              </div>
            )}

            <div>
              <label className="frequency-label">Alert Frequency:</label>
              <select
                value={settings.alertFrequency}
                onChange={(e) => updateSetting('alertFrequency', e.target.value)}
              >
                <option value="Any Change">Any Change</option>
                <option value="Daily">Daily Summary</option>
                <option value="Weekly">Weekly Summary</option>
              </select>
            </div>

          </div>
        )}

      </div>

      {hasChanges && (
        <div className="form-actions">
          <button
            onClick={handleSave}
            disabled={status.loading}
            className="btn-save"
          >
            {status.loading ? 'Saving...' : 'Save Preferences'}
          </button>

          <button
            onClick={handleCancel}
            disabled={status.loading}
            className="btn-cancel"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
