import requests, re
import boto3
from geopy.geocoders import Nominatim

WIND_ALERT_THRESHOLD = 25
RAIN_ALERT_THRESHOLD = 50
HEAT_ALERT_THRESHOLD = 102

def getRain(day):
    alerts = []
    rainProbability = day['probabilityOfPrecipitation']['value']
    if isinstance(rainProbability, int) and rainProbability > RAIN_ALERT_THRESHOLD:
        alerts.append(f"Rain likely on {day['name']}: {day['shortForecast']}")
    return alerts

def getWind(day):
    alerts = []
    windString = day["windSpeed"]
    windSpeed = re.findall(r'\d+', windString)
    if any(int(wind) > WIND_ALERT_THRESHOLD for wind in windSpeed):
        alerts.append(f"High winds on {day['name']}. Batten down the hatches!")
    return alerts

def getHeat(day):
    alerts = []
    temperature = day["temperature"]
    if int(temperature) > HEAT_ALERT_THRESHOLD:
        alerts.append(f"Heat warning on {day['name']}. {temperature}F Stay cool!")
    return alerts


def lambda_handler(event, context):
    query_params = event.get("queryStringParameters") or {}
    city = query_params.get("city")

    if not city:
        return {
            "statusCode": 400,
            "body": "Missing required query parameter: city"
        }
    geolocator = Nominatim(user_agent="weather_lambda_app")

    try:
        location = geolocator.geocode(city)
        if not location:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "*",  # Or specify a domain instead of "*"
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type"
                },
                "body": "Missing required query parameter: city"
            }

        lat, long = location.latitude, location.longitude
        url = f'https://api.weather.gov/points/{lat},{long}'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        forecast_url = response.json()['properties']['forecast']

        forecast_response = requests.get(forecast_url, timeout=10)
        forecast_response.raise_for_status()
        forecast = forecast_response.json()["properties"]["periods"]

        alerts = []
        for day in forecast[:7]:  
            alerts += getRain(day)
            alerts += getWind(day)
            alerts += getHeat(day)

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",  # Or specify a domain instead of "*"
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": "\n".join(alerts) if alerts else f"No weather alerts for {city}."
        }

    except requests.exceptions.RequestException as e:
        return {
            "statusCode": 502,
            "body": f"Network error while fetching forecast: {str(e)}"
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Unexpected error: {str(e)}"
        }
