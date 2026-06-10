import { useState, useEffect } from 'react';
import { useAuthenticator } from '@aws-amplify/ui-react';
import { fetchAuthSession } from 'aws-amplify/auth';
import { API_BASE } from './api';

export default function ManageAlerts() {
  const { user } = useAuthenticator((context) => [context.user]);
  
  // 1. UPDATED STATE: Perfectly aligned with the backend keys
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

  // Fetch settings on mount
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

        // 2. Map data securely to our aligned keys
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

  // Check if any field on the entire form has been modified
  const hasChanges = originalSettings && 
    JSON.stringify(settings) !== JSON.stringify(originalSettings);

  const updateSetting = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    // Clear success message when user starts typing again
    if (status.message) setStatus(prev => ({ ...prev, message: null }));
  };

  // 3. THE SINGLE SAVE ACTION
  const handleSave = async () => {
    setStatus({ loading: true, error: null, message: null });

    // Quick client-side validation
    const cityRegex = /^[A-Za-z\s.'-]+$/;
    if (settings.city && !cityRegex.test(settings.city)) {
      setStatus({ loading: false, error: 'City name can only contain letters, spaces, hyphens, and apostrophes.', message: null });
      return;
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
      
      // Update local settings with the standardized city from the backend
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
    return <div className="manage_alerts"><p>Loading settings...</p></div>;
  }

  return (
    <div className="manage_alerts">
      <h2>Manage Weather Alerts</h2>

      {status.error && <p style={{ color: 'red', fontWeight: 'bold' }}>{status.error}</p>}
      {status.message && <p style={{ color: 'green', fontWeight: 'bold' }}>{status.message}</p>}

      {/* THE NEW FORM UI */}
      <div className="settings-form" style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '400px', margin: '0 auto', textAlign: 'left' }}>
        
        {/* City Input */}
        <div>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>Tracked City:</label>
          <input
            type="text"
            placeholder="e.g., Seattle"
            value={settings.city}
            onChange={(e) => updateSetting('city', e.target.value)}
            style={{ width: '100%', padding: '8px' }}
          />
        </div>

        <hr style={{ width: '100%', border: '0.5px solid #ccc' }} />

        {/* Master Alert Switch */}
        <div>
          <label style={{ fontWeight: 'bold', fontSize: '1.1rem', cursor: 'pointer' }}>
            <input 
              type="checkbox"
              checked={settings.alertsEnabled}
              onChange={(e) => updateSetting('alertsEnabled', e.target.checked)}
              style={{ marginRight: '10px' }}
            />
            Enable Weather Alerts
          </label>
        </div>

        {/* Nested Alert Preferences */}
        {settings.alertsEnabled && (
          <div style={{ marginLeft: '25px', display: 'flex', flexDirection: 'column', gap: '15px' }}>
            
            <div>
              <label style={{ cursor: 'pointer' }}>
                <input 
                  type="checkbox"
                  checked={settings.emailEnable}
                  onChange={(e) => updateSetting('emailEnable', e.target.checked)}
                  style={{ marginRight: '10px' }}
                />
                Receive Email Alerts
              </label>
            </div>

            <div>
              <label style={{ cursor: 'pointer' }}>
                <input 
                  type="checkbox"
                  checked={settings.smsEnable}
                  onChange={(e) => updateSetting('smsEnable', e.target.checked)}
                  style={{ marginRight: '10px' }}
                />
                Receive Text Messages
              </label>
            </div>

            {/* Conditionally show Phone Number input if texts are enabled */}
            {settings.smsEnable && (
              <div style={{ marginLeft: '25px' }}>
                <label style={{ display: 'block', fontSize: '0.9rem', marginBottom: '5px' }}>Phone Number:</label>
                <input 
                  type="tel"
                  placeholder="+1234567890"
                  value={settings.phoneNumber}
                  onChange={(e) => updateSetting('phoneNumber', e.target.value)}
                  style={{ width: '100%', padding: '8px' }}
                />
              </div>
            )}

            <div>
              <label style={{ display: 'block', marginBottom: '5px' }}>Alert Frequency:</label>
              <select 
                value={settings.alertFrequency}
                onChange={(e) => updateSetting('alertFrequency', e.target.value)}
                style={{ width: '100%', padding: '8px' }}
              >
                <option value="Any Change">Any Change</option>
                <option value="Daily">Daily Summary</option>
                <option value="Weekly">Weekly Summary</option>
              </select>
            </div>
            
          </div>
        )}

      </div>

      {/* The Global Action Buttons */}
      {hasChanges && (
        <div style={{ marginTop: '30px', display: 'flex', gap: '10px', justifyContent: 'center' }}>
          <button 
            onClick={handleSave} 
            disabled={status.loading}
            style={{ padding: '10px 20px', cursor: 'pointer', backgroundColor: '#F9980B', color: 'white', border: 'none', borderRadius: '4px' }}
          >
            {status.loading ? 'Saving...' : 'Save Preferences'}
          </button>
          
          <button 
            onClick={handleCancel} 
            disabled={status.loading}
            style={{ padding: '10px 20px', cursor: 'pointer', backgroundColor: '#ccc', border: 'none', borderRadius: '4px' }}
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}