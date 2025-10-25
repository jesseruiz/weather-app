import React from 'react';
import { useState } from 'react';
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
  const [result, setResult] = useState("");
  const [alertType, setAlertType] = useState("default");
  const [alertIcon, setAlertIcon] = useState("");
  

  async function getWeather() {
    if (!city) {
      setResult("No city entered. Please enter a valid city");
      return;
    }
    try {
      const response = await fetch(
        `https://raj8a28np4.execute-api.us-east-1.amazonaws.com/weather?city=${encodeURIComponent(city)}`
      );
      const text = await response.text();
      setResult(text);

      lowerText = text.toLowerCase();

      // Basic keyword matching
      if (lowerText.includes("heat")) {
        setAlertType("heat");
        setAlertIcon(heatIcon);
      } else if (lowerText.includes("wind")) {
        setAlertType("windy");
        setAlertIcon(windIcon);
      } else if (lowerText.includes("rain")) {
        setAlertType("rain");
        setAlertIcon(rainIcon);
      } else {
        setAlertType("default");
      }


    } catch (error) {
      setResult("Error fetching weather: " + error.message);
      setAlertType("heat");
      setAlertIcon(rainIcon);
    }
  }

  return (
    <div className={`home ${alertType}`}>
      <div className={`mainContent ${result ? 'shifted' : ''}`}>
        <h1 className="mainHeader">Check Weather Alerts</h1>
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
      </div>

      {result && (
        <div className={`responseCard alert-container ${alertType}`}>
          {alertIcon && <img src={alertIcon} alt="Alert icon" />}
          <div className="responseContent">
            <p className="result">{result}</p>
            {weatherAnimations[alertType] && (
              <DotLottieReact
                src={weatherAnimations[alertType]}
                loop
                autoplay
                className="weather-lottie-background"
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
