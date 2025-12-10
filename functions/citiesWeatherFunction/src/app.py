import requests
import boto3
from geopy.geocoders import Nominatim
from datetime import datetime
from boto3.dynamodb.conditions import Key


#Ultimately will scan user db table for cities and get weather for each

# Setup DynamoDB table resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('weather-app-cities')

# Cities to process
cities = set()

def get_cities():
    try:
        response = table.scan(
            ProjectionExpression='city'  # Only get the city attribute
        )

        for item in response.get('Items'):
            cities.add(item['city'])

        return list(cities)


    except Exception as e:
        print(f"Error with DynamoDB scan: {e}")


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

        weekly_forecast = data["properties"]["periods"]
        filtered_periods = [weekly_forecast[0]] + [p for p in weekly_forecast[1:] if p.get("isDaytime")]
        filtered_periods = filtered_periods[:7]
        print('Filtered')
        print(filtered_periods)
        formatted_forecast = []
        for day in filtered_periods:

            rain_probability = day['probabilityOfPrecipitation']['value']
            wind_speed = day["windSpeed"]
            temperature = day["temperature"]

            formatted_forecast.append({
                'day': day['name'],
                'date': day['startTime'].split('T')[0],  # Extract date only
                'temperature': temperature,
                'windSpeed': wind_speed,
                'rainProbability': rain_probability,
            })
            print(formatted_forecast)
        
        store_weather_data_weekly(city, formatted_forecast)

    except (requests.exceptions.RequestException, KeyError) as e:
        print(f"Weather unavailable for {city}. Error: {e}")


def store_weather_data_daily(city, temperature, wind_speed, rain_probability):
    print('Starting')
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

def store_weather_data_weekly(city, forecast):
    table.put_item(
        Item={
            'city': city,
            'forecastType': 'weekly',
            'timestamp': datetime.utcnow().isoformat(),
            'weeklyForecast': forecast
        }
    )


def lambda_handler(event, context):

    get_cities()


    for city in cities:
        lat, long = get_city_coordinates(city)
        if lat and long:
            get_weather(lat, long, city)

    return {
        'statusCode': 200,
        'body': 'Weather data loaded successfully'
    }
