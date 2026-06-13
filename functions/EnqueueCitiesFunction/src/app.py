import json
import boto3
import requests
from geopy.geocoders import Nominatim
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
city_table = dynamodb.Table('weather-app-cities')

def filter_forecast_periods(all_periods):
    return [
        p for i, p in enumerate(all_periods)
        if i < 2 or (p.get('isDaytime') is True and "night" not in p.get('name', '').lower())
    ]

def lambda_handler(event, context):
    geolocator = Nominatim(user_agent="weather_lambda_app", timeout=5)

    for record in event.get('Records', []):
        city_data = json.loads(record['body'])
        city_name = city_data.get('city')

        if not city_name:
            continue

        print(f"WORKER: Fetching weather for {city_name}")

        try:
            location = geolocator.geocode(city_name)
            if not location:
                print(f"Could not find {city_name}")
                continue

            lat, long = location.latitude, location.longitude

            url = f'https://api.weather.gov/points/{lat},{long}'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            forecast_url = response.json()['properties']['forecast']

            forecast_response = requests.get(forecast_url, timeout=10)
            forecast_response.raise_for_status()
            all_periods = forecast_response.json()["properties"]["periods"]

            weekly_forecast = []
            for day in filter_forecast_periods(all_periods)[:8]:
                rain_prob = day.get('probabilityOfPrecipitation', {}).get('value')
                weekly_forecast.append({
                    "name": day.get("name", "Unknown"),
                    "temperature": day.get("temperature", "N/A"),
                    "windSpeed": day.get("windSpeed", "N/A"),
                    "rainProbability": rain_prob if rain_prob is not None else 0,
                    "shortForecast": day.get("shortForecast", "")
                })

            if weekly_forecast:
                city_table.put_item(
                    Item={
                        'city': city_name,
                        'forecastType': 'weekly',
                        'timestamp': datetime.utcnow().isoformat(),
                        'currentTemperature': weekly_forecast[0]['temperature'],
                        'currentWind': weekly_forecast[0]['windSpeed'],
                        'currentRainProbability': weekly_forecast[0]['rainProbability'],
                        'weeklyForecast': weekly_forecast
                    }
                )
                print(f"SUCCESS: {city_name} updated.")

        except Exception as e:
            print(f"Failed to process {city_name}: {e}")
            # Re-raise so SQS knows this message failed and retries it
            raise

    return {"statusCode": 200, "body": "Success"}
