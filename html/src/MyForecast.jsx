import { useState } from 'react';
import "./MyForecast.css";

export default function MyForecast({ forecast }) {
  const [selectedDay, setSelectedDay] = useState(
    forecast && forecast.length > 0 ? forecast[0].name : null
  );

  if (!forecast || forecast.length === 0) {
    return <p>No weekly data available.</p>;
  }

  return (
    <div className="weekly-forecast">
      <div className="forecast-grid">
        {forecast.map((item) => (
          <div
            key={item.name}
            className={`forecast-card ${selectedDay === item.name ? 'selected' : ''}`}
            onClick={() => setSelectedDay(item.name)}
            role="button"
            tabIndex={0}
            aria-pressed={selectedDay === item.name}
            onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && setSelectedDay(item.name)}
          >
            <h3 className="forecast-day">{item.name}</h3>
            <p className="forecast-desc">{item.shortForecast}</p>
            <div className="forecast-stats">
              <span className="temp">{item.temperature}°F</span>
              <span className="rain"><span aria-hidden="true">💧</span><span className="sr-only">Rain: </span>{item.rainProbability}%</span>
              <span className="wind"><span aria-hidden="true">💨</span><span className="sr-only">Wind: </span>{item.windSpeed}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
