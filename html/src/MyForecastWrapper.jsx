import { useEffect, useState } from "react";
import { useAuthenticator } from "@aws-amplify/ui-react";
import { fetchAuthSession } from "aws-amplify/auth";
import { API_BASE } from "./api";
import MyForecast from "./MyForecast";

export default function MyForecastWrapper() {
  const { authStatus, user } = useAuthenticator(
    (ctx) => [ctx.authStatus, ctx.user]
  );
  
  const [loading, setLoading] = useState(true);
  const [forecastData, setForecastData] = useState(null); 
  const [city, setCity] = useState("");

  useEffect(() => {
    async function fetchForecast() {
      if (authStatus !== "authenticated" || !user) return;
      const id = user.username; 

      try {
        const session = await fetchAuthSession();
        const token = session.tokens?.idToken?.toString(); 

        if (!token) return;

        const res = await fetch(
          `${API_BASE}/weekly?id=${encodeURIComponent(id)}`,
          {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );
        
        const data = await res.json();

        if (Array.isArray(data) && data.length > 0) {
          const forecastObject = data[0];
          setCity(forecastObject.city);
          setForecastData(forecastObject);
        }
      } catch (error) {
        console.error("Error fetching weather:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchForecast();
  }, [authStatus, user]); 

  if (authStatus === "configuring") return <p>Loading authentication...</p>;
  if (authStatus !== "authenticated") return <p>User not signed in.</p>;
  if (loading) return <p>Loading weather...</p>;

  return (
    <div className="forecast-wrapper">
      <h1 className="forecast-title">Forecast for {city || "your area"}</h1>

      {forecastData && (
        <p className="current-conditions">
          <strong>Right Now:</strong> {forecastData.currentTemperature}°F | 💨 {forecastData.currentWind} | 💧 {forecastData.currentRainProbability}%
        </p>
      )}

      {forecastData?.weeklyForecast ? (
        <MyForecast forecast={forecastData.weeklyForecast} />
      ) : (
        <p>No forecast data found.</p>
      )}
    </div>
  );
}