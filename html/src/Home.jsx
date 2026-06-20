import React, { useState } from 'react';
import { fetchAuthSession } from 'aws-amplify/auth';
import { API_BASE } from './api';
import './Home.css';

const ALERT_LABELS = {
  heat: 'Heat Alert',
  rain: 'Rain Alert',
  wind: 'Wind Alert',
};

const CONDITIONS = [
  { key: 'hotter',  label: 'Hotter than forecast', emoji: '🌡️' },
  { key: 'colder',  label: 'Colder than forecast',  emoji: '🥶' },
  { key: 'raining', label: 'Raining',               emoji: '🌧️' },
  { key: 'windy',   label: 'Windier than forecast',  emoji: '💨' },
  { key: 'fine',    label: 'Looks fine',             emoji: '☀️' },
];

const CROWDSOURCE_LABELS = {
  hotter:  'hotter than forecast',
  colder:  'colder than forecast',
  raining: 'raining',
  windy:   'windier than forecast',
  fine:    'looking fine',
};

function parseAlertDays(alerts) {
  const days = {};
  alerts.forEach(alert => {
    const match = alert.match(/on (\w+)/);
    if (!match) return;
    const day = match[1];
    if (alert.startsWith('Heat')) days[day] = 'heat';
    else if (alert.startsWith('Rain')) days[day] = 'rain';
    else if (alert.startsWith('High winds')) days[day] = 'wind';
  });
  return days;
}

export default function Home() {
  const [city, setCity] = useState("");
  const [resultCity, setResultCity] = useState("");
  const [alerts, setAlerts] = useState([]);
  const [forecast, setForecast] = useState([]);
  const [crowdsource, setCrowdsource] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [reportPicking, setReportPicking] = useState(false);
  const [reportSubmitted, setReportSubmitted] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);

  async function getWeather() {
    if (!city) {
      setErrorMsg("No city entered. Please enter a valid city");
      return;
    }

    setErrorMsg("");
    setAlerts([]);
    setForecast([]);
    setCrowdsource(null);
    setHasSearched(false);
    setReportPicking(false);
    setReportSubmitted(false);
    setLoading(true);

    try {
      const response = await fetch(
        `${API_BASE}/weather?city=${encodeURIComponent(city)}`
      );

      const data = await response.json();

      if (data.error) {
         setErrorMsg(data.error);
         return;
      }

      setAlerts(data.alerts || []);
      setForecast(data.forecast || []);
      setResultCity(data.city || city);
      setCrowdsource(data.crowdsource || null);
      setHasSearched(true);

    } catch (error) {
      setErrorMsg("Error fetching weather: " + error.message);
    } finally {
      setLoading(false);
    }
  }

  async function submitReport(condition) {
    setReportLoading(true);
    try {
      const today = new Date().toISOString().split('T')[0];
      const headers = { 'Content-Type': 'application/json' };

      try {
        const session = await fetchAuthSession();
        const token = session.tokens?.idToken?.toString();
        if (token) headers['Authorization'] = `Bearer ${token}`;
      } catch (_) {
        // Not logged in — submit anonymously
      }

      await fetch(`${API_BASE}/report`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ city: resultCity, condition, date: today })
      });

      setReportSubmitted(true);
      setReportPicking(false);
    } catch (err) {
      console.error('Failed to submit report:', err);
      setReportPicking(false);
    } finally {
      setReportLoading(false);
    }
  }

  const alertDays = parseAlertDays(alerts);

  return (
    <div className="home">
      <div className={`main-content ${hasSearched ? 'shifted' : ''}`}>
        <h1 className={`main-header ${hasSearched ? 'compact' : ''}`}>Check Weather Alerts & Forecast</h1>
        <div className="submit-field">
          <input
            className="input-field"
            type="text"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="City or City, State (e.g. Springfield, IL)"
            onKeyDown={(e) => e.key === 'Enter' && getWeather()}
          />
          <button className="submit-button" onClick={getWeather} disabled={loading}>
            {loading ? 'Loading...' : 'Get Weather'}
          </button>
        </div>
        {errorMsg && <p className="error-text">{errorMsg}</p>}
      </div>

      {hasSearched && (
        <div className="response-card">
          <div className="response-content">
            <div className="forecast-section">
              <h2>7-Day Forecast for {resultCity}</h2>
              <div className="forecast-grid">
                {forecast.map((day, index) => {
                  const alertType = alertDays[day.name];
                  const isToday = index === 0;
                  return (
                    <div key={index} className={`forecast-card ${alertType ? `has-alert-${alertType}` : ''}`}>
                      {isToday && crowdsource && (
                        <span className="crowdsource-badge">
                          🏘️ Locals say: {CROWDSOURCE_LABELS[crowdsource.condition]}
                        </span>
                      )}
                      {alertType && (
                        <span className={`alert-badge alert-badge-${alertType}`}>
                          {ALERT_LABELS[alertType]}
                        </span>
                      )}
                      <h3 className="forecast-day">{day.name}</h3>
                      <p className="forecast-desc">{day.shortForecast}</p>
                      <div className="forecast-stats">
                        <span className="temp">{day.temperature}°F</span>
                        <span className="rain">💧 {day.rainProbability}%</span>
                        <span className="wind">💨 {day.windSpeed}</span>
                      </div>
                      {isToday && (
                        <div className="report-section">
                          {reportSubmitted ? (
                            <p className="report-thanks">Thanks for the report!</p>
                          ) : reportPicking ? (
                            <div className="report-picker">
                              {CONDITIONS.map(c => (
                                <button
                                  key={c.key}
                                  className="report-option"
                                  onClick={() => submitReport(c.key)}
                                  disabled={reportLoading}
                                >
                                  {c.emoji} {c.label}
                                </button>
                              ))}
                              <button className="report-cancel" onClick={() => setReportPicking(false)}>
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <button className="report-trigger" onClick={() => setReportPicking(true)}>
                              Not for me
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
