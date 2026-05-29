import json
import boto3
import requests
from geopy.geocoders import Nominatim
from datetime import datetime

# Setup DynamoDB
dynamodb = boto3.resource('dynamodb')
city_table = dynamodb.Table('weather-app-cities')

def lambda_handler(event, context):
    geolocator = Nominatim(user_agent="weather_lambda_app")
    
    # SQS sends messages in batches under the 'Records' key
    for record in event.get('Records', []):
        # The body contains the city name we sent
        city_data = json.loads(record['body'])
        city_name = city_data.get('city')
        
        if not city_name:
            continue
            
        print(f"WORKER: Fetching weather for {city_name}")
        
        try:
            # 1. Get Lat/Long
            location = geolocator.geocode(city_name)
            if not location:
                print(f"Could not find {city_name}")
                continue
                
            lat, long = location.latitude, location.longitude
            
            # 2. Fetch NWS Data
            url = f'https://api.weather.gov/points/{lat},{long}'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            forecast_url = response.json()['properties']['forecast']

            forecast_response = requests.get(forecast_url, timeout=10)
            forecast_response.raise_for_status()
            all_periods = forecast_response.json()["properties"]["periods"]

            # Filter Daytime periods
            weekly_forecast = []
            custom_periods = [p for i, p in enumerate(all_periods) if i < 2 or (p.get('isDaytime') is True and "night" not in p.get('name', '').lower())]
            
            for day in custom_periods[:8]:
                rain_prob = day.get('probabilityOfPrecipitation', {}).get('value')
                weekly_forecast.append({
                    "name": day.get("name", "Unknown"), 
                    "temperature": day.get("temperature", "N/A"),
                    "windSpeed": day.get("windSpeed", "N/A"),
                    "rainProbability": rain_prob if rain_prob is not None else 0,
                    "shortForecast": day.get("shortForecast", "")
                })

            # 3. Save back to DynamoDB
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
            # If we raise an exception, SQS knows it failed and will retry it later!
            raise e

    return {"statusCode": 200, "body": "Success"}