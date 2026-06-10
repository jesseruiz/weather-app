import React, { useState } from 'react';
import { DotLottieReact } from '@lottiefiles/dotlottie-react';
import { useAuthenticator } from '@aws-amplify/ui-react';
import { API_BASE } from './api';
import './Home.css';

const weatherAnimations = {
    rain: "./Rainy.lottie",
    windy: "./wind.lottie",
    heat: "./ThermometerHot.lottie",
};

export default function Home() {
  const { authStatus, user } = useAuthenticator((authState) => [authState.authStatus, authState.user]);
  
  const [city, setCity] = useState("");
  const [alerts, setAlerts] = useState([]);
  const [forecast, setForecast] = useState([]);
  const [errorMsg, setErrorMsg] = useState("");
  const [alertType, setAlertType] = useState("default");
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

      // Save the specific data into state
      setAlerts(data.alerts || []);
      setForecast(data.forecast || []);
      setHasSearched(true);

      // Combine alerts into a single string just to check for Lottie animation keywords
      const lowerText = (data.alerts || []).join(" ").toLowerCase();

      if (lowerText.includes("heat")) {
        setAlertType("heat");
      } else if (lowerText.includes("wind")) {
        setAlertType("windy");
      } else if (lowerText.includes("rain")) {
        setAlertType("rain");
      } else {
        setAlertType("default");
      }

    } catch (error) {
      setErrorMsg("Error fetching weather: " + error.message);
      setAlertType("default");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={`home ${alertType}`}>
      <div className={`mainContent ${hasSearched ? 'shifted' : ''}`}>
        <h1 className="mainHeader">Check Weather Alerts & Forecast</h1>
        <div className='submitField'>
          <input
            className="inputField"
            type="text"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="Enter city (e.g., Los Angeles)"
          />
          <button className="submitButton" onClick={getWeather} disabled={loading}>
            {loading ? 'Loading...' : 'Get Weather'}
          </button>
        </div>
        {errorMsg && <p className="error-text" style={{color: 'red', marginTop: '10px'}}>{errorMsg}</p>}
      </div>

      {hasSearched && (
        <div className={`responseCard alert-container ${alertType}`}>
          <div className="responseContent">
            
            {/* TIER 1: Active Alerts & Lottie Side-by-Side */}
            {alerts.length > 0 && (
              <div className="alerts-section">
                
                {/* Left Side: The Text */}
                <div className="alerts-text">
                  <h2>Active Alerts</h2>
                  <ul className="alerts-list">
                    {alerts.map((alert, index) => (
                      <li key={index} className="alert-item">{alert}</li>
                    ))}
                  </ul>
                </div>

                {/* Right Side: The Lottie Animation */}
                {weatherAnimations[alertType] && alertType !== "default" && (
                  <div className="lottie-container">
                    <DotLottieReact
                      src={weatherAnimations[alertType]}
                      loop
                      autoplay
                    />
                  </div>
                )}
                
              </div>
            )}

            {/* TIER 2: Horizontal 7-Day Forecast Grid */}
            <div className="forecast-section">
              <h2>7-Day Forecast</h2>
              <div className="forecast-grid">
                {forecast.map((day, index) => (
                  <div key={index} className="forecast-card">
                    <h3 className="forecast-day">{day.name}</h3>
                    <p className="forecast-desc">{day.shortForecast}</p>
                    <div className="forecast-stats">
                      <span className="temp">{day.temperature}°F</span>
                      <span className="rain">💧 {day.rainProbability}%</span>
                      <span className="wind">💨 {day.windSpeed}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}