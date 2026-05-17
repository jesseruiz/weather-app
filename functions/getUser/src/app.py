import boto3
import json
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('weather-app-table')

HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
}

# Ensure DynamoDB Decimal types don't crash JSON dumps
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def checkUser(user_id):
    response = table.get_item(Key={'id': user_id})
    if 'Item' not in response:
        return {} # Return empty dict if user hasn't saved settings yet
    
    return response['Item']

def lambda_handler(event, context):
    # 1. Safely intercept HTTP API OPTIONS request
    http_method = event.get("httpMethod")
    if not http_method:
        http_method = event.get("requestContext", {}).get("http", {}).get("method")

    if http_method == 'OPTIONS':
        return {'statusCode': 200, 'headers': HEADERS, 'body': ''}

    query_params = event.get("queryStringParameters") or {}
    user_id = query_params.get("id")

    if not user_id:
        return {'statusCode': 400, 'headers': HEADERS, 'body': json.dumps({'error': 'Missing user id'})}
    
    try:
        user = checkUser(user_id)

        return {
            'statusCode': 200,
            'headers': HEADERS,
            'body': json.dumps(user, default=decimal_default)
        }

    except Exception as e:
        print(f"Error: {e}")
        return {'statusCode': 500, 'headers': HEADERS, 'body': json.dumps({'error': str(e)})}