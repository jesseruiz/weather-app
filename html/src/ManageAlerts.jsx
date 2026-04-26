import { useState, useEffect } from 'react';
import { useAuthenticator } from '@aws-amplify/ui-react';
import { fetchAuthSession } from 'aws-amplify/auth'; // 1. Import the session fetcher

export default function ManageAlerts() {
  const { user } = useAuthenticator((context) => [context.user]);
  
  const [settings, setSettings] = useState({
    city: '',
    alertsEnabled: false,
    emailEnable: false,
    textEnable: false,
    alertFrequency: 'Any Change'
  });
  
  const [originalSettings, setOriginalSettings] = useState(null);
  const [status, setStatus] = useState({ loading: true, error: null, message: null });
  const [editingCity, setEditingCity] = useState(false);
  const [cityInput, setCityInput] = useState('');

  // Fetch settings on mount
  useEffect(() => {
    if (!user?.username) return;

    // 2. Refactor to an async function to easily grab the token before fetching
    async function fetchSettings() {
      try {
        const session = await fetchAuthSession();
        const token = session.tokens?.idToken?.toString();

        if (!token) throw new Error("No valid auth token found.");

        const res = await fetch(`https://raj8a28np4.execute-api.us-east-1.amazonaws.com/get_user?id=${user.username}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`, // 3. Inject secure token
            'Content-Type': 'application/json'
          }
        });

        if (!res.ok) throw new Error('Failed to fetch settings');
        
        const data = await res.json();

        const fetchedSettings = {
          city: data.city || '',
          alertsEnabled: data.alerts || false,
          emailEnable: data["alerts-email"] ? true : false,
          textEnable: data["alerts-text"] ? true : false,
          alertFrequency: data["alert-frequency"] || 'None'
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

  // Check if there are unsaved changes
  const hasChanges = originalSettings && 
    JSON.stringify(settings) !== JSON.stringify(originalSettings);

  const updateSetting = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const validateCity = (value) => {
    const cityRegex = /^[A-Za-z\s.'-]+$/;
    return value && cityRegex.test(value);
  };

  const handleCityEdit = () => {
    setCityInput(settings.city);
    setEditingCity(true);
  };

  const handleCitySave = () => {
    if (!validateCity(cityInput)) {
      setStatus({ ...status, error: 'City name can only contain letters, spaces, hyphens, and apostrophes.' });
      return;
    }
    updateSetting('city', cityInput);
    setEditingCity(false);
    setStatus({ ...status, error: null });
  };

  const handleCityCancel = () => {
    setCityInput('');
    setEditingCity(false);
    setStatus({ ...status, error: null });
  };

  const handleSave = async () => {
    setStatus({ loading: true, error: null, message: null });

    try {
      // 4. Grab the secure token again before saving data
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();

      if (!token) throw new Error("No valid auth token found.");

      const response = await fetch('https://raj8a28np4.execute-api.us-east-1.amazonaws.com/update_user', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` // 5. Inject secure token
        },
        body: JSON.stringify({ ...settings, userId: user?.username })
      });

      if (!response.ok) throw new Error('Failed to save');

      setOriginalSettings(settings);
      setStatus({ loading: false, error: null, message: 'Settings saved successfully!' });
    } catch (err) {
      setStatus({ loading: false, error: err.message, message: null });
    }
  };

  const handleCancel = () => {
    setSettings(originalSettings);
    setCityInput('');
    setEditingCity(false);
    setStatus({ ...status, error: null, message: null });
  };

  if (status.loading && !originalSettings) {
    return <div className="manage_alerts"><p>Loading settings...</p></div>;
  }

  return (
    <div className="manage_alerts">
      <h2>Manage Weather Alerts</h2>

      {/* Status Messages */}
      {status.error && <p style={{ color: 'red' }}>{status.error}</p>}
      {status.message && <p style={{ color: 'green' }}>{status.message}</p>}

      {/* City Setting */}
      <div style={{ marginBottom: '20px' }}>
        <p><strong>City:</strong> {settings.city || 'Not set'}</p>
        {!editingCity ? (
          <button onClick={handleCityEdit}>Update City</button>
        ) : (
          <div>
            <input
              type="text"
              placeholder="Enter city name"
              value={cityInput}
              onChange={(e) => setCityInput(e.target.value)}
            />
            <button onClick={handleCitySave}>Save City</button>
            <button onClick={handleCityCancel}>Cancel</button>
          </div>
        )}
      </div>

      {/* Enable Alerts */}
      <div>
        <label>
          <input 
            type="checkbox"
            checked={settings.alertsEnabled}
            onChange={(e) => updateSetting('alertsEnabled', e.target.checked)}
          />
          Enable Alerts
        </label>
      </div>

      {/* Conditional Alert Options */}
      {settings.alertsEnabled && (
        <>
          <div>
            <label>
              <input 
                type="checkbox"
                checked={settings.emailEnable}
                onChange={(e) => updateSetting('emailEnable', e.target.checked)}
              />
              Email Alerts
            </label>
          </div>

          <div>
            <label>
              <input 
                type="checkbox"
                checked={settings.textEnable}
                onChange={(e) => updateSetting('textEnable', e.target.checked)}
              />
              Text Alerts
            </label>
          </div>

          <div>
            <label>Alert Frequency:</label>
            <select 
              value={settings.alertFrequency}
              onChange={(e) => updateSetting('alertFrequency', e.target.value)}
            >
              <option value="Any">Any Change</option>
              <option value="Daily">Daily Summary</option>
              <option value="Weekly">Weekly Summary</option>
            </select>
          </div>
        </>
      )}

      {/* Save/Cancel Buttons */}
      {hasChanges && (
        <div style={{ marginTop: '20px' }}>
          <button onClick={handleSave} disabled={status.loading}>
            {status.loading ? 'Saving...' : 'Save Changes'}
          </button>
          <button onClick={handleCancel} disabled={status.loading}>
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}