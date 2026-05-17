import boto3
import json

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('weather-app-table')
citiesWeather = dynamodb.Table('weather-app-cities')
sqs = boto3.client('sqs')
ses = boto3.client('ses')
QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/745167176709/Weather-Alerts'

def getUserWeather(city):
    try:
        # 1. FIXED: Change 'daily' to 'weekly'
        response = citiesWeather.get_item(
            Key={'city': city, 'forecastType': 'weekly'}
        )
        item = response.get('Item')
        if not item:
            print(f"No weather found for {city}")
            return None
        return item
    except Exception as e:
        print(f"Error getting weather for {city}: {e}")
        return None

def send_weather_email(email, weather_data):
    try:
        # 2. FIXED: Pull directly from the new top-level database attributes
        city             = weather_data['city']
        temperature      = int(weather_data['currentTemperature'])
        wind_speed       = weather_data['currentWind']
        rain_probability = int(weather_data['currentRainProbability'])

        if rain_probability > 70:
            condition_emoji = "🌧️ Rainy"
        elif rain_probability > 40:
            condition_emoji = "⛅ Partly Cloudy"
        else:
            condition_emoji = "☀️ Clear"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px;">
            <h2 style="color: #2c3e50;">🌤️ Daily Weather Report — {city}</h2>
            <div style="background-color: #f0f4f8; border-radius: 10px; padding: 20px;">
                <h3 style="color: #2980b9;">{condition_emoji}</h3>
                <table style="width: 100%; font-size: 16px;">
                    <tr><td>🌡️ <strong>Temperature</strong></td><td>{temperature}°F</td></tr>
                    <tr><td>💨 <strong>Wind Speed</strong></td><td>{wind_speed}</td></tr>
                    <tr><td>🌧️ <strong>Rain Probability</strong></td><td>{rain_probability}%</td></tr>
                </table>
            </div>
        </body>
        </html>
        """

        ses.send_email(
            Source='weather@rainforthee.com',
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {'Data': f"🌤️ Your Daily Weather Report for {city}"},
                'Body':    {'Html': {'Data': html_body}}
            }
        )
        print(f"Email sent to {email}")
    except Exception as e:
        print(f"Error sending email to {email}: {e}")



def lambda_handler(event, context):
    try:
        # ── Step 1: Unpack all records from SQS ───────────────────────────────
        # Each record is one user: { email: ..., city: ... }
        users = []
        for record in event['Records']:
            data = json.loads(record['body'])
            users.append({
                'email': data['email'],
                'city':  data['city']
            })

        # ── Step 2: Deduplicate cities ────────────────────────────────────────
        # Build a unique set of cities across all users in this batch
        # e.g. 10 users in Seattle → only fetch Seattle's weather once
        unique_cities = set(user['city'] for user in users)

        # ── Step 3: Fetch weather once per unique city ────────────────────────
        # Store results in a dict so we can reuse them
        # e.g. { 'Seattle': { temp: 47, wind: ... }, 'Austin': { ... } }
        weather_cache = {}
        for city in unique_cities:
            weather = getUserWeather(city)
            if weather:
                weather_cache[city] = weather

        # ── Step 4: Send each user their email using the cached weather ────────
        for user in users:
            city    = user['city']
            email   = user['email']

            if city not in weather_cache:
                print(f"Skipping {email} — no weather data for {city}")
                continue

            send_weather_email(email, weather_cache[city])

    except Exception as e:
        print(f"Error in lambda_handler: {e}")
