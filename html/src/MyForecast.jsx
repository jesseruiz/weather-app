import { useState } from 'react';
import "./MyForecast.css";


export default function MyForecast({forecast}) {
  const today = forecast[0].day;
  const [selectedDay, setSelectedDay] = useState(today);



  return (
    <div className="weekly-forecast">
      {/* Header */}
      <h1 className="forecast-title">Weekly Forecast</h1>

      {/* Top: 7 cards */}
      <div className="forecast-card-row">
          {forecast.map((item) => (
            <div
              key={item.day}
              className={`forecast-card ${selectedDay === item.day ? "selected" : ""}`}
              onClick={() => setSelectedDay(item.day)}
            >
              <div className="day-label">{item.day}</div>
              <div className="weather-icon-placeholder"></div>
              <div className="temp-placeholder">Temp: {item.temperature}°F</div>
              <div className="wind-placeholder">Wind: {item.windSpeed}</div>
              <div className="rain-placeholder">Rain: {item.rainProbability}%</div>
            </div>
          ))}
      </div>
    </div>
  );
    
}