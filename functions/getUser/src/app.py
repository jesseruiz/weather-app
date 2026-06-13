import boto3
import json
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('weather-app-table')

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def checkUser(user_id):
    response = table.get_item(Key={'id': user_id})
    return response.get('Item')

def lambda_handler(event, context):
    query_params = event.get("queryStringParameters") or {}
    user_id = query_params.get("id")

    if not user_id:
        return {'statusCode': 400, 'body': json.dumps({'error': 'Missing user id'})}

    try:
        user = checkUser(user_id)
        if user is None:
            return {'statusCode': 404, 'body': json.dumps({'error': 'User not found'})}
        return {'statusCode': 200, 'body': json.dumps(user, default=decimal_default)}

    except Exception as e:
        print(f"Error: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error'})}
