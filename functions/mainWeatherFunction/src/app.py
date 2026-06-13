import requests
import re
import json
import os
import boto3
from geopy.geocoders import Nominatim
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('weather-app-cities')

WIND_ALERT_THRESHOLD = int(os.environ.get('WIND_ALERT_THRESHOLD', '25'))
RAIN_ALERT_THRESHOLD = int(os.environ.get('RAIN_ALERT_THRESHOLD', '50'))
HEAT_ALERT_THRESHOLD = int(os.environ.get('HEAT_ALERT_THRESHOLD', '102'))

def filter_forecast_periods(all_periods):
    return [
        p for i, p in enumerate(all_periods)
        if i < 2 or (p.get('isDaytime') is True and "night" not in p.get('name', '').lower())
    ]

def getRain(day):
    alerts = []
    rainProbability = day.get('probabilityOfPrecipitation', {}).get('value') or 0
    if isinstance(rainProbability, (int, Decimal, float)) and float(rainProbability) > RAIN_ALERT_THRESHOLD:
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

def decimal_default(obj):
    if isinstance(obj, Decimal): return float(obj)
    raise TypeError

def lambda_handler(event, context):
    query_params = event.get("queryStringParameters") or {}
    raw_city = query_params.get("city")

    if not raw_city:
        return {'statusCode': 400, 'body': json.dumps({"error": "Missing city"})}

    normalized_city = raw_city.strip().title()

    # Check cache first
    try:
        response = table.get_item(Key={'city': normalized_city, 'forecastType': 'weekly'})
        cached_item = response.get('Item')

        if cached_item:
            print(f"CACHE HIT: Loading {normalized_city} from DynamoDB")
            weekly_forecast = cached_item.get('weeklyForecast', [])

            alerts = []
            for day in weekly_forecast[:8]:
                alerts += getRain(day)
                alerts += getWind(day)
                alerts += getHeat(day)

            return {
                "statusCode": 200,
                "body": json.dumps({
                    "city": normalized_city,
                    "alerts": alerts,
                    "forecast": weekly_forecast
                }, default=decimal_default)
            }
    except Exception as e:
        print(f"Cache check failed, falling back to NWS API: {e}")

    # Cache miss — fetch from NWS
    print(f"CACHE MISS: Fetching {normalized_city} from NWS API")
    geolocator = Nominatim(user_agent="weather_lambda_app", timeout=5)

    try:
        location = geolocator.geocode(normalized_city)
        if not location:
            return {'statusCode': 400, 'body': json.dumps({"error": f"Could not find a valid location for '{normalized_city}'."})}

        lat, long = location.latitude, location.longitude

        url = f'https://api.weather.gov/points/{lat},{long}'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        forecast_url = response.json()['properties']['forecast']

        forecast_response = requests.get(forecast_url, timeout=10)
        forecast_response.raise_for_status()
        all_periods = forecast_response.json()["properties"]["periods"]

        alerts = []
        weekly_forecast = []
        for day in filter_forecast_periods(all_periods)[:8]:
            alerts += getRain(day)
            alerts += getWind(day)
            alerts += getHeat(day)

            rain_prob = day.get('probabilityOfPrecipitation', {}).get('value')
            weekly_forecast.append({
                "name": day.get("name", "Unknown"),
                "temperature": day.get("temperature", "N/A"),
                "windSpeed": day.get("windSpeed", "N/A"),
                "rainProbability": rain_prob if rain_prob is not None else 0,
                "shortForecast": day.get("shortForecast", "")
            })

        if weekly_forecast:
            try:
                table.put_item(
                    Item={
                        'city': normalized_city,
                        'forecastType': 'weekly',
                        'timestamp': datetime.utcnow().isoformat(),
                        'currentTemperature': weekly_forecast[0]['temperature'],
                        'currentWind': weekly_forecast[0]['windSpeed'],
                        'currentRainProbability': weekly_forecast[0]['rainProbability'],
                        'weeklyForecast': weekly_forecast
                    }
                )
                print(f"CACHE WRITE: Saved {normalized_city} to database for future queries.")
            except Exception as e:
                print(f"Failed to write to cache: {e}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "city": normalized_city,
                "alerts": alerts,
                "forecast": weekly_forecast
            })
        }

    except requests.exceptions.RequestException as e:
        return {'statusCode': 502, 'body': json.dumps({"error": "Network error while fetching forecast."})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({"error": f"Unexpected error: {str(e)}"})}
