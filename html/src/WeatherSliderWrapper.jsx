import { useEffect, useState } from 'react';
import Slider from './Slider'; // path to your slider
// import './Slider.css'; // make sure styles are applied here or in CardSlider

const WEATHER_API = 'https://raj8a28np4.execute-api.us-east-1.amazonaws.com/cards'; // your actual API Gateway URL

export default function WeatherSliderWrapper() {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchWeather() {
      try {
        const res = await fetch(WEATHER_API);
        const data = await res.json();

        // Transform weather objects into card format
        const formatted = data.map((item) => ({
          id: item.city,
          title: item.city,
          description: `
            Temp: ${item.temperature}°F
            Rain: ${item.rainProbability}%
            Wind: ${item.windSpeed}
          `
        }));

        setCards(formatted);
      } catch (error) {
        console.error('Error fetching weather:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchWeather();
  }, []);

  if (loading) return <p>Loading weather...</p>;

  return (
    <Slider cards={cards} visibleCount={2} />
  );
}
