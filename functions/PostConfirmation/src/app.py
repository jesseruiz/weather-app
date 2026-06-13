import boto3
import json
import requests
from botocore.exceptions import ClientError
from geopy.geocoders import Nominatim
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
user_table = dynamodb.Table('weather-app-table')
city_table = dynamodb.Table('weather-app-cities')

def filter_forecast_periods(all_periods):
    return [
        p for i, p in enumerate(all_periods)
        if i < 2 or (p.get('isDaytime') is True and "night" not in p.get('name', '').lower())
    ]

def lambda_handler(event, context):
    print("Post Confirmation Event:")
    print(json.dumps(event, indent=2))

    user_attributes = event['request']['userAttributes']

    user_id = user_attributes.get('sub')  
    email = user_attributes.get('email')
    raw_city = user_attributes.get('custom:City', '')
    
    # Normalize the city name (e.g. "seattle" -> "Seattle")
    normalized_city = raw_city.strip().title() if raw_city else "Unknown"

    # ==========================================
    # 1. CREATE USER PROFILE IN DATABASE
    # ==========================================
    try:
        put_response = user_table.put_item(
            Item={
                'id': user_id,
                'email': email,
                'city': normalized_city,
                'emailEnable': False,
                'smsEnable': False,
                'alertsEnabled': False,
                'alertFrequency': 'Any Change'
            },
        )
        print("PutItem response:", put_response)
    except ClientError as e:
        print("Failed to save user:", e.response['Error']['Message'])
        raise


    # ==========================================
    # 2. CHECK CACHE FOR CITY & FETCH IF MISSING
    # ==========================================
    if normalized_city and normalized_city != "Unknown":
        try:
            # Check if the city already exists in the cache
            response = city_table.get_item(Key={'city': normalized_city, 'forecastType': 'weekly'})
            if 'Item' in response:
                print(f"CACHE HIT: {normalized_city} already tracked.")
                return event # City exists, we are completely done!
        except Exception as e:
            print(f"Cache check error: {e}")

        # Cache Miss - Fetch from Weather API
        print(f"CACHE MISS: Fetching {normalized_city} for new user...")
        geolocator = Nominatim(user_agent="weather_lambda_app")
        
        try:
            location = geolocator.geocode(normalized_city)
            if location:
                lat, long = location.latitude, location.longitude
                
                # Fetch NWS Data
                url = f'https://api.weather.gov/points/{lat},{long}'
                weather_res = requests.get(url, timeout=10)
                weather_res.raise_for_status()
                forecast_url = weather_res.json()['properties']['forecast']

                forecast_res = requests.get(forecast_url, timeout=10)
                forecast_res.raise_for_status()
                all_periods = forecast_res.json()["properties"]["periods"]

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

                # Write the new city to the database
                if weekly_forecast:
                    city_table.put_item(
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
                    print(f"SUCCESS: {normalized_city} cached to DynamoDB.")
                    
        except Exception as e:
            print(f"Failed to fetch/cache weather for new city: {e}")

    # Cognito triggers MUST return the original event untouched
    return event