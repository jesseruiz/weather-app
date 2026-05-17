// src/MyForecastWrapper.jsx
import { useEffect, useState } from "react";
import { useAuthenticator } from "@aws-amplify/ui-react";
import { fetchAuthSession } from "aws-amplify/auth";
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
          `https://raj8a28np4.execute-api.us-east-1.amazonaws.com/weekly?id=${encodeURIComponent(id)}`,
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
    <div style={{ textAlign: 'center', padding: '20px' }}>
      <h1>Forecast for {city || "your area"}</h1>
      
      {/* NEW: Displaying the top-level stats we just added to the DB! */}
      {forecastData && (
        <div style={{ margin: '20px 0', fontSize: '1.2rem', color: '#F9980B' }}>
            <p><strong>Right Now:</strong> {forecastData.currentTemperature}°F | 💨 {forecastData.currentWind} | 💧 {forecastData.currentRainProbability}%</p>
        </div>
      )}

      {forecastData?.weeklyForecast ? (
        <MyForecast forecast={forecastData.weeklyForecast} />
      ) : (
        <p>No forecast data found.</p>
      )}
    </div>
  );
}