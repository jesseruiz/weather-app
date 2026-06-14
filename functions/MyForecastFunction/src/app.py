import boto3
import json
from decimal import Decimal
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
user_table = dynamodb.Table('weather-app-table')
city_table = dynamodb.Table('weather-app-cities')


def getUserCity(usrID):
    try:
        response = user_table.query(KeyConditionExpression=Key("id").eq(str(usrID)))
        items = response.get('Items', [])
        if not items:
            print(f"No user record found for id: {usrID}")
            return None
        return items[0]['city']
    except Exception as e:
        print(f"Error querying user city: {e}")
        return None

def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj

def getWeather(city):
    try:
        response = city_table.query(
            KeyConditionExpression=Key("city").eq(city) & Key("forecastType").eq("weekly")
        )
        return response['Items']
    except Exception as e:
        print(f"Error querying weather: {e}")
        return None

def lambda_handler(event, context):
    try:
        query_params = event.get("queryStringParameters") or {}
        usrID = query_params.get("id")

        if not usrID:
            return {'statusCode': 400, 'body': json.dumps({"error": "Missing id in query parameters"})}

        city = getUserCity(usrID)
        if not city:
            return {'statusCode': 404, 'body': json.dumps({"error": "User city not found"})}

        result = getWeather(city)
        if result is None:
            return {'statusCode': 500, 'body': json.dumps({"error": "Failed to fetch weather data"})}

        capped = []
        for item in result:
            if 'weeklyForecast' in item:
                item['weeklyForecast'] = item['weeklyForecast'][:7]
            capped.append(item)
        return {'statusCode': 200, 'body': json.dumps(convert_decimals(capped))}

    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {'statusCode': 500, 'body': json.dumps({"error": "Internal Server Error"})}
