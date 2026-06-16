import React, { useState } from 'react';
import { API_BASE } from './api';
import './Home.css';

const ALERT_LABELS = {
  heat: 'Heat Alert',
  rain: 'Rain Alert',
  wind: 'Wind Alert',
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
  const [alerts, setAlerts] = useState([]);
  const [forecast, setForecast] = useState([]);
  const [errorMsg, setErrorMsg] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [loading, setLoading] = useState(false);

  async function getWeather() {
    if (!city) {
      setErrorMsg("No city entered. Please enter a valid city");
      return;
    }

    setErrorMsg("");
    setAlerts([]);
    setForecast([]);
    setHasSearched(false);
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
      setHasSearched(true);

    } catch (error) {
      setErrorMsg("Error fetching weather: " + error.message);
    } finally {
      setLoading(false);
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
              <h2>7-Day Forecast</h2>
              <div className="forecast-grid">
                {forecast.map((day, index) => {
                  const alertType = alertDays[day.name];
                  return (
                    <div key={index} className={`forecast-card ${alertType ? `has-alert-${alertType}` : ''}`}>
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
