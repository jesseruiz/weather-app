import boto3
import json
from decimal import Decimal

#Need to update to query for specific cities instead of scanning whole db

def decimal_default(obj):
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    raise TypeError

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('weather-app-cities')

def lambda_handler(event, context):
    try:
        response = table.scan()
        items = response.get('Items', [])
    except Exception as e:
        print(f"Error scanning DynamoDB: {e}")
        return {'statusCode': 500, 'body': json.dumps({"error": "Failed to fetch weather data"})}

    return {'statusCode': 200, 'body': json.dumps(items, default=decimal_default)}
