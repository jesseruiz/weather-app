import json
import boto3
import requests
from geopy.geocoders import Nominatim
from datetime import datetime

# Initialize the DynamoDB resource
dynamodb = boto3.resource('dynamodb')
user_table = dynamodb.Table('weather-app-table')
cities_table = dynamodb.Table('weather-app-cities')

def lambda_handler(event, context):
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,PUT'
    }
    
    try:
        if not event.get('body'):
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Missing request body'})
            }
            
        body = json.loads(event['body'])
        
        # Extract the Cognito ID from the payload
        user_id = body.get('userId') or body.get('username')

        if not user_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Cognito User ID is a required field.'})
            }

        # 1. Handle City Validation & Caching ONLY if a new city was provided
        city_name = body.get('city')
        standardized_city_name = None

        if city_name:
            print(f"City update detected for ID {user_id}: {city_name}. Validating...")
            geolocator = Nominatim(user_agent="weather_lambda_app")
            location = geolocator.geocode(city_name)
            
            if not location:
                return {
                    'statusCode': 400,
                    'headers': cors_headers,
                    'body': json.dumps({'error': f"Could not find city '{city_name}'. Please check your spelling."})
                }
            
            lat, long = location.latitude, location.longitude
            standardized_city_name = location.address.split(',')[0].strip()

            # Verify/Seed the weather-app-cities cache table
            cache_check = cities_table.get_item(
                Key={
                    'city': standardized_city_name,
                    'forecastType': 'weekly'
                }
            )
            
            if 'Item' not in cache_check:
                try:
                    url = f'https://api.weather.gov/points/{lat},{long}'
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    forecast_url = response.json()['properties']['forecast']

                    forecast_response = requests.get(forecast_url, timeout=10)
                    forecast_response.raise_for_status()
                    all_periods = forecast_response.json()["properties"]["periods"]

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

                    if weekly_forecast:
                        cities_table.put_item(
                            Item={
                                'city': standardized_city_name,
                                'forecastType': 'weekly',
                                'timestamp': datetime.utcnow().isoformat(),
                                'currentTemperature': weekly_forecast[0]['temperature'], 
                                'currentWind': weekly_forecast[0]['windSpeed'],
                                'currentRainProbability': weekly_forecast[0]['rainProbability'], 
                                'weeklyForecast': weekly_forecast
                            }
                        )
                except Exception as nws_error:
                    print(f"Warning: Failed to seed cache for {standardized_city_name}: {str(nws_error)}")

        # 2. Build a Dynamic Update Expression for the user profile table
        update_parts = ["SET updatedAt = :u"]
        expr_values = {':u': datetime.utcnow().isoformat()}
        
        # Maps incoming payload keys to database field names
        fields_to_map = {
            'email': 'email',              
            'emailEnable': 'emailEnable',
            'smsEnable': 'smsEnable',
            'phoneNumber': 'phoneNumber'
        }

        # Check for optional profile fields in the payload
        for incoming_key, db_field in fields_to_map.items():
            if incoming_key in body:
                update_parts.append(f"{db_field} = :{incoming_key}")
                expr_values[f":{incoming_key}"] = body[incoming_key]

        # If a validated city exists, add it to the update statement
        if standardized_city_name:
            update_parts.append("city = :c")
            expr_values[':c'] = standardized_city_name

        update_expression = ", ".join(update_parts)

        # 3. Executing the surgical update using 'id' as the primary key
        print(f"Executing surgical update for user ID {user_id} with Expression: {update_expression}")
        user_table.update_item(
            Key={'id': user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expr_values
        )

        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'message': 'Profile settings updated successfully.',
                'city': standardized_city_name if standardized_city_name else "Unchanged"
            })
        }

    except Exception as e:
        print(f"Critical error in updateUser: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            # Removed the temp error string logic here. Safe, generic message for the user!
            'body': json.dumps({'error': 'An internal server error occurred while updating your profile.'}) 
        }