// MyForecastWrapper.jsx
import { useEffect, useState } from "react";
import { useAuthenticator } from "@aws-amplify/ui-react";
import { fetchAuthSession } from "aws-amplify/auth"; // 1. Import the session fetcher
import MyForecast from "./MyForecast";

export default function MyForecastWrapper() {
  const { authStatus, user } = useAuthenticator(
    (ctx) => [ctx.authStatus, ctx.user]
  );
  
  const [loading, setLoading] = useState(true);
  const [forecastData, setForecastData] = useState(null); 
  const [city, setCity] = useState("");

  console.log("Component Render - Current forecastData:", forecastData);

  useEffect(() => {
    async function fetchForecast() {
      if (authStatus !== "authenticated" || !user) return;

      const id = user.username; 
      
      console.log("Attempting to fetch forecast for User ID:", id);

      try {
        // 2. Fetch the auth session to get the current user's secure tokens
        const session = await fetchAuthSession();
        
        // 3. Extract the ID token (you can also use accessToken depending on your API setup)
        const token = session.tokens?.idToken?.toString(); 

        if (!token) {
            console.error("No valid auth token found. User may need to sign in again.");
            return;
        }

        // 4. Pass the token in the Authorization header
        const res = await fetch(
          `https://raj8a28np4.execute-api.us-east-1.amazonaws.com/weekly?id=${encodeURIComponent(id)}`,
          {
            method: 'GET', // Good practice to explicitly declare the method
            headers: {
              'Authorization': `Bearer ${token}`, // Injecting the JWT
              'Content-Type': 'application/json'
            }
          }
        );
        
        const data = await res.json();

        console.log("Raw API Response Data:", data);

        if (Array.isArray(data) && data.length > 0) {
          const forecastObject = data[0];
          
          console.log("Extracted Forecast Object:", forecastObject);

          setCity(forecastObject.city);
          setForecastData(forecastObject);
        } else {
          console.warn("API returned an empty array or unexpected format.", data);
        }
      } catch (error) {
        console.error("Error fetching weather:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchForecast();
  }, [authStatus, user]); 

  // UI State Handlers
  if (authStatus === "configuring") return <p>Loading authentication...</p>;
  if (authStatus !== "authenticated") return <p>User not signed in.</p>;
  if (loading) return <p>Loading weather...</p>;

  return (
    <div>
      <h1>Forecast for {city || "your area"}</h1>
      {forecastData?.weeklyForecast ? (
        <MyForecast forecast={forecastData.weeklyForecast} />
      ) : (
        <p>No forecast data found.</p>
      )}
    </div>
  );
}