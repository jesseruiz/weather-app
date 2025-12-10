import boto3
import json
from decimal import Decimal
from boto3.dynamodb.conditions import Key


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

    usrID = event["queryStringParameters"]["id"]
    city = getUserCity(usrID)
    result = getWeather(city)


    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",  # or specific origin
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
        },
        "body": json.dumps(convert_decimals(result))
    }


