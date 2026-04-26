import React, { useState } from 'react';
import { DotLottieReact } from '@lottiefiles/dotlottie-react';
import { useAuthenticator } from '@aws-amplify/ui-react';
import './Home.css';

const weatherAnimations = {
    rain: "./Rainy.lottie",
    windy: "./wind.lottie",
    heat: "./ThermometerHot.lottie",
};

export default function Home() {
  const { authStatus, user } = useAuthenticator((authState) => [authState.authStatus, authState.user]);
  const [city, setCity] = useState("");
  
  // Updated state to handle complex objects instead of a single string
  const [alerts, setAlerts] = useState([]);
  const [forecast, setForecast] = useState([]);
  const [errorMsg, setErrorMsg] = useState("");
  const [alertType, setAlertType] = useState("default");  
  const [hasSearched, setHasSearched] = useState(false);

  async function getWeather() {
    if (!city) {
      setErrorMsg("No city entered. Please enter a valid city");
      return;
    }
    
    // Reset state before fetching
    setErrorMsg("");
    setAlerts([]);
    setForecast([]);
    setHasSearched(false);

    try {
      const response = await fetch(
        `https://raj8a28np4.execute-api.us-east-1.amazonaws.com/weather?city=${encodeURIComponent(city)}`
      );
      
      // Parse JSON instead of Text
      const data = await response.json();

      if (data.error) {
         setErrorMsg(data.error);
         return;
      }

      setAlerts(data.alerts || []);
      setForecast(data.forecast || []);
      setHasSearched(true);

      // Combine alerts into a single string to check for keywords
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
    }
  }

  return (
    <div className={`home ${alertType}`}>
      <div className={`mainContent ${hasSearched ? 'shifted' : ''}`}>
        <h1 className="mainHeader">Check Weather</h1>
        <div className='submitField'>
          <input
            className="inputField"
            type="text"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="Enter city (e.g., Los Angeles)"
          />
          <button className="submitButton" onClick={getWeather}>Get Weather</button>
        </div>
        {errorMsg && <p className="error-text" style={{color: 'red'}}>{errorMsg}</p>}
      </div>

      {hasSearched && (
        <div className={`responseCard alert-container ${alertType}`}>
          <div className="responseContent" style={{ zIndex: 2, position: 'relative' }}>
            
            {/* Alerts Section */}
            <div className="alerts-section">
              <h2>Active Alerts</h2>
              {alerts.length > 0 ? (
                <ul>
                  {alerts.map((alert, index) => (
                    <li key={index} className="alert-item">{alert}</li>
                  ))}
                </ul>
              ) : (
                <p>No active weather alerts for this area.</p>
              )}
            </div>

            {/* Forecast Section */}
            <div className="forecast-section" style={{ marginTop: '20px' }}>
              <h2>7-Day Forecast</h2>
              <div className="forecast-grid" style={{ display: 'grid', gap: '10px', maxHeight: '400px', overflowY: 'auto' }}>
                {forecast.map((day, index) => (
                  <div key={index} className="forecast-card" style={{ padding: '10px', background: 'rgba(255,255,255,0.8)', borderRadius: '8px' }}>
                    <strong>{day.name}</strong>: {day.shortForecast} <br/>
                    Temp: {day.temperature}°F | Wind: {day.windSpeed} | Rain: {day.rainProbability}%
                  </div>
                ))}
              </div>
            </div>

          </div>
          
          {/* Lottie Background */}
          {weatherAnimations[alertType] && alertType !== "default" && (
            <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: 1, opacity: 0.5, pointerEvents: 'none' }}>
              <DotLottieReact
                src={weatherAnimations[alertType]}
                loop
                autoplay
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}