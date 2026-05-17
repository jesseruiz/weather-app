import boto3
import json
from decimal import Decimal
from boto3.dynamodb.conditions import Key

HEADERS = {
    "Access-Control-Allow-Origin": "*",  
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
}


def getUserCity(usrID):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('weather-app-table')

    try:
        response = table.query(
            KeyConditionExpression=Key("id").eq(str(usrID))
        )

        city = response['Items'][0]['city']

        return city

    except Exception as e:
        print(f"Error with query DynamoDB: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to fetch weather data"})
        }

def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj

def getWeather(city):

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('weather-app-cities')

    try:
        response = table.query(
            KeyConditionExpression=Key("city").eq(city) & Key("forecastType").eq("weekly")
        )
        forecast = response['Items']

        return forecast


    except Exception as e:
        print(f"Error with query DynamoDB: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to fetch weather data"})
        }


def lambda_handler(event, context):
    # 2. Extract the HTTP Method (Handles both REST APIs and HTTP APIs safely)
    http_method = event.get("httpMethod")
    if not http_method:
        http_method = event.get("requestContext", {}).get("http", {}).get("method")

    # 3. INTERCEPT OPTIONS REQUEST: Return 200 OK immediately with headers
    if http_method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": HEADERS,
            "body": ""
        }

    # --- Only process actual GET requests below this line ---
    try:
        # Safely extract query parameters so missing params don't crash the Lambda
        query_params = event.get("queryStringParameters") or {}
        usrID = query_params.get("id")

        if not usrID:
            return {
                "statusCode": 400,
                "headers": HEADERS,
                "body": json.dumps({"error": "Missing id in query parameters"})
            }

        city = getUserCity(usrID)
        
        # Handle cases where the user exists but hasn't set a city yet
        if not city:
            return {
                "statusCode": 404,
                "headers": HEADERS,
                "body": json.dumps({"error": "User city not found"})
            }

        result = getWeather(city)

        return {
            "statusCode": 200,
            "headers": HEADERS,
            "body": json.dumps(convert_decimals(result))
        }
        
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {
            "statusCode": 500,
            "headers": HEADERS,
            "body": json.dumps({"error": "Internal Server Error"})
        }

