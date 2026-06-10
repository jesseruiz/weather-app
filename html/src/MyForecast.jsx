import { useState } from 'react';
import "./MyForecast.css";

export default function MyForecast({ forecast }) {
  // Guard Clause: If forecast is missing or empty, stop here.
  if (!forecast || forecast.length === 0) {
    return <p>No weekly data available.</p>;
  }
  
  // 1. UPDATED: Target .name instead of .day for the default selection
  const [selectedDay, setSelectedDay] = useState(forecast[0].name);

  return (
    <div className="weekly-forecast">
      <h1 className="forecast-title">Weekly Forecast</h1>

      <div className="forecast-card-row">
        {forecast.map((item) => (
          <div
            key={item.name} /* 2. UPDATED: Use item.name for the key */
            className={`forecast-card ${selectedDay === item.name ? "selected" : ""}`}
            onClick={() => setSelectedDay(item.name)} /* 3. UPDATED: Set state using item.name */
          >
            <div className="day-label">{item.name}</div>
            <div className="weather-icon-placeholder"></div>
            
            {/* These already perfectly match your new optimized backend! */}
            <div className="temp-placeholder">Temp: {item.temperature}°F</div>
            <div className="wind-placeholder">Wind: {item.windSpeed}</div>
            <div className="rain-placeholder">Rain: {item.rainProbability}%</div>
          </div>
        ))}
      </div>

      <div className="selected-details">
        <h3>Showing details for: {selectedDay}</h3>
      </div>
    </div>
  );
}