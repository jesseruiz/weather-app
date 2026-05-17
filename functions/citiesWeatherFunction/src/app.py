import requests
import boto3
from geopy.geocoders import Nominatim
from datetime import datetime

# Setup DynamoDB table resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('weather-app-cities')

# Geolocator setup
geolocator = Nominatim(user_agent="weather_app")

def get_cities():
    """Scans DynamoDB and returns a list of unique cities."""
    cities = set()
    try:
        response = table.scan(
            ProjectionExpression='city' 
        )
        for item in response.get('Items', []):
            cities.add(item['city'])
            
        return list(cities)
    except Exception as e:
        print(f"Error with DynamoDB scan: {e}")
        return []

def get_city_coordinates(city):
    location = geolocator.geocode(city)
    if location:
        return location.latitude, location.longitude
    else:
        print(f"City not found: {city}")
        return None, None

def get_weather(lat, long, city):
    try:
        print(f"Fetching weather for {city}...")
        url = f'https://api.weather.gov/points/{lat},{long}'
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        forecast_url = data['properties']['forecast']

        r = requests.get(forecast_url)
        r.raise_for_status()
        data = r.json()

        weekly_forecast = data["properties"]["periods"]
        # Grab the current period + the next 6 daytime periods
        filtered_periods = [weekly_forecast[0]] + [p for p in weekly_forecast[1:] if p.get("isDaytime")]
        filtered_periods = filtered_periods[:7]
        
        formatted_forecast = []
        for day in filtered_periods:
            formatted_forecast.append({
                'name': day['name'], # Changed from 'day' to 'name' to match your React frontend!
                'date': day['startTime'].split('T')[0],
                'temperature': day["temperature"],
                'windSpeed': day["windSpeed"],
                'rainProbability': day.get('probabilityOfPrecipitation', {}).get('value') or 0,
            })
        
        # ONE single database write per city!
        store_weather_data(city, formatted_forecast)

    except (requests.exceptions.RequestException, KeyError) as e:
        print(f"Weather unavailable for {city}. Error: {e}")

def store_weather_data(city, forecast):
    """Stores the full 7-day forecast. Daily data is simply forecast[0]."""
    print(f"Storing optimized forecast for {city}...")
    
    table.put_item(
        Item={
            'city': city,
            'forecastType': 'weekly', # Kept as 'weekly' so frontend API doesn't break
            'timestamp': datetime.utcnow().isoformat(),
            'currentTemperature': forecast[0]['temperature'], 
            'currentWind': forecast[0]['windSpeed'],
            'currentRainProbability': forecast[0]['rainProbability'], 
            'weeklyForecast': forecast
        }
    )

def lambda_handler(event, context):
    cities = get_cities()

    for city in cities:
        lat, long = get_city_coordinates(city)
        if lat and long:
            get_weather(lat, long, city)

    return {
        'statusCode': 200,
        'body': 'Weather data optimized and loaded successfully'
    }