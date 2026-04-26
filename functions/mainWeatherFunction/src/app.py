import requests
import re
import json
import boto3
from geopy.geocoders import Nominatim

WIND_ALERT_THRESHOLD = 25
RAIN_ALERT_THRESHOLD = 50
HEAT_ALERT_THRESHOLD = 102

def getRain(day):
    alerts = []
    # Safely get the rain probability, default to 0 if missing
    rainProbability = day.get('probabilityOfPrecipitation', {}).get('value') or 0
    if isinstance(rainProbability, int) and rainProbability > RAIN_ALERT_THRESHOLD:
        alerts.append(f"Rain likely on {day['name']}: {day['shortForecast']}")
    return alerts

def getWind(day):
    alerts = []
    windString = day.get("windSpeed", "")
    windSpeed = re.findall(r'\d+', windString)
    if any(int(wind) > WIND_ALERT_THRESHOLD for wind in windSpeed):
        alerts.append(f"High winds on {day['name']}. Batten down the hatches!")
    return alerts

def getHeat(day):
    alerts = []
    temperature = day.get("temperature", 0)
    if int(temperature) > HEAT_ALERT_THRESHOLD:
        alerts.append(f"Heat warning on {day['name']}. {temperature}F Stay cool!")
    return alerts


def lambda_handler(event, context):
    query_params = event.get("queryStringParameters") or {}
    city = query_params.get("city")

    # Standardize headers for a JSON response with CORS enabled
    headers = {
        "Access-Control-Allow-Origin": "*",  
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Content-Type": "application/json"
    }

    if not city:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Missing required query parameter: city"})
        }
        
    geolocator = Nominatim(user_agent="weather_lambda_app")

    try:
        location = geolocator.geocode(city)
        if not location:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": f"Could not find location for {city}"})
            }

        lat, long = location.latitude, location.longitude
        
        # Step 1: Get the NWS gridpoints for the lat/long
        url = f'https://api.weather.gov/points/{lat},{long}'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        forecast_url = response.json()['properties']['forecast']

        # Step 2: Fetch the actual forecast data
        forecast_response = requests.get(forecast_url, timeout=10)
        forecast_response.raise_for_status()
        
        all_periods = forecast_response.json()["properties"]["periods"]

        alerts = []
        weekly_forecast = []
        
        # Step 3: Aggressively filter for the immediate 24 hours + subsequent days
        custom_periods = []
        for index, period in enumerate(all_periods):
            if index < 2:
                # Always grab the first two periods (Day 1 + Night 1)
                custom_periods.append(period)
            else:
                # For everything else, strictly enforce daytime.
                # 1. isDaytime MUST be explicitly True
                is_daytime_flag = period.get('isDaytime') is True
                
                # 2. Fallback: string matching to ensure "night" isn't in the name
                name_lower = period.get('name', '').lower()
                has_night_in_name = "night" in name_lower or "overnight" in name_lower
                
                if is_daytime_flag and not has_night_in_name:
                    custom_periods.append(period)
        
        # We grab 8 items total (2 immediate periods + 6 future days)
        for day in custom_periods[:8]:  
            # 1. Build the alerts array
            alerts += getRain(day)
            alerts += getWind(day)
            alerts += getHeat(day)
            
            # 2. Build the forecast UI array
            rain_prob = day.get('probabilityOfPrecipitation', {}).get('value')
            weekly_forecast.append({
                "name": day.get("name", "Unknown"), 
                "temperature": day.get("temperature", "N/A"),
                "windSpeed": day.get("windSpeed", "N/A"),
                "rainProbability": rain_prob if rain_prob is not None else 0,
                "shortForecast": day.get("shortForecast", "")
            })

        # Step 4: Construct the final payload
        response_body = {
            "city": city,
            "alerts": alerts,
            "forecast": weekly_forecast
        }

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps(response_body)
        }

    except requests.exceptions.RequestException as e:
        return {
            "statusCode": 502,
            "headers": headers,
            "body": json.dumps({"error": f"Network error while fetching forecast: {str(e)}"})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": f"Unexpected error: {str(e)}"})
        }