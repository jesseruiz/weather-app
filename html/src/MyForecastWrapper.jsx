import { useEffect, useState } from "react";
import { useAuthenticator } from "@aws-amplify/ui-react";
import MyForecast from "./MyForecast";

export default function MyForecastWrapper() {
  const { authStatus, user, signOut } = useAuthenticator(
    (ctx) => [ctx.authStatus, ctx.user]
  );
  const [loading, setLoading] = useState(true);
  const [forecast, setForecast] = useState("")
  const [city, setCity] = useState("")
  const [userid, setUserid] = useState("");

  useEffect(() => {
    async function fetchForecast() {
      if (authStatus !== "authenticated" || !user) return;

      const id = user.username; 
      setUserid(id);

      try {
        const res = await fetch(
          `https://raj8a28np4.execute-api.us-east-1.amazonaws.com/weekly?id=${encodeURIComponent(
            id
          )}`
        );
        const data = await res.json();
        console.log(data[0])

        setCity(data[0].city)
        setForecast(data[0])
      } catch (error) {
        console.error("Error fetching weather:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchForecast();
  }, [authStatus, user]); 

  if (authStatus === "configuring") {
    return <p>Loading authentication...</p>;
  }

  if (authStatus !== "authenticated" || !user) {
    return <p>User not signed in.</p>;
  }

  if (loading) {
    return <p>Loading weather...</p>;
  }

  return (
    <div>
        <h1>Forecast for {city}</h1>
        <MyForecast forecast={forecast.weeklyForecast} />
    </div>
  );
}
