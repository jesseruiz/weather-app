import { useState } from 'react';
import "./MyForecast.css";

export default function MyForecast({ forecast }) {
  // 1. Guard Clause: If forecast is missing or empty, stop here.
  if (!forecast || forecast.length === 0) {
    return <p>No weekly data available.</p>;
  }
  
  // Target the first index of the array for initialization
  const [selectedDay, setSelectedDay] = useState(forecast[0].day);

  return (
    <div className="weekly-forecast">
      <h1 className="forecast-title">Weekly Forecast</h1>

      <div className="forecast-card-row">
        {forecast.map((item) => (
          <div
            key={item.day}
            className={`forecast-card ${selectedDay === item.day ? "selected" : ""}`}
            onClick={() => setSelectedDay(item.day)}
          >
            <div className="day-label">**{item.day}**</div>
            <div className="weather-icon-placeholder"></div>
            <div className="temp-placeholder">Temp: {item.temperature}°F</div>
            <div className="wind-placeholder">Wind: {item.windSpeed}</div>
            <div className="rain-placeholder">Rain: {item.rainProbability}%</div>
          </div>
        ))}
      </div>

      {/* Optional: Add a detail view for the selected day */}
      <div className="selected-details">
        <h3>Showing details for: {selectedDay}</h3>
      </div>
    </div>
  );
}