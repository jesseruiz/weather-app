import requests
import boto3
from geopy.geocoders import Nominatim
from datetime import datetime

# Setup DynamoDB table resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('weather-app-cities')

# Cities to process
CITIES = {'Los Angeles', 'New York City', 'Chicago', 'Houston', 'Seattle', 'Nashville', 'Miami'}

# Geolocator setup
geolocator = Nominatim(user_agent="weather_app")


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

        daily_forecast = data["properties"]["periods"][0]
        rain_probability = daily_forecast['probabilityOfPrecipitation']['value']
        wind_speed = daily_forecast["windSpeed"]
        temperature = daily_forecast["temperature"]

        print(f"{city}: {temperature}F, {wind_speed}, {rain_probability}% chance of rain")

        store_weather_data_daily(city, temperature, wind_speed, rain_probability)

        weekly_forecast = data["properties"]["periods"][1:6]
        for day in weekly_forecast:
            formatted_forecast = []

            rain_probability = daily_forecast['probabilityOfPrecipitation']['value']
            wind_speed = daily_forecast["windSpeed"]
            temperature = daily_forecast["temperature"]

            formatted_forecast.append({
                'day': day['name'],
                'date': day['startTime'].split('T')[0],  # Extract date only
                'temperature': temperature,
                'windSpeed': wind_speed,
                'rainProbability': rain_probability,
            })

            store_weather_data_weekly(city, formatted_forecast)

    except (requests.exceptions.RequestException, KeyError) as e:
        print(f"Weather unavailable for {city}. Error: {e}")


def store_weather_data_daily(city, temperature, wind_speed, rain_probability):
    table.put_item(
        Item={
            'city': city,
            'forecastType': 'daily',
            'timestamp': datetime.utcnow().isoformat(),
            'dailyForecast': {
                'temperature': temperature,
                'windSpeed': wind_speed,
                'rainProbability': rain_probability,
            }
        }
    )

def store_weather_data_weekly(city, forcast):
    table.put_item(
        Item={
            'city': city,
            'forecastType': 'weekly',
            'timestamp': datetime.utcnow().isoformat(),
            'weeklyForecast': forcast
        }
    )


def lambda_handler(event, context):
    for city in CITIES:
        lat, long = get_city_coordinates(city)
        if lat and long:
            get_weather(lat, long, city)

    return {
        'statusCode': 200,
        'body': 'Weather data loaded successfully'
    }