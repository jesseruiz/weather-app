import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('weather-app-table')

HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token',
    'Access-Control-Allow-Methods': 'POST, OPTIONS'
}

def lambda_handler(event, context):
    # 1. Safely intercept HTTP API OPTIONS request
    http_method = event.get("httpMethod")
    if not http_method:
        http_method = event.get("requestContext", {}).get("http", {}).get("method")

    if http_method == 'OPTIONS':
        return {'statusCode': 200, 'headers': HEADERS, 'body': ''}
    
    try:
        body = json.loads(event['body'])
        
        user_id = body.get('userId')
        if not user_id:
            return {'statusCode': 400, 'headers': HEADERS, 'body': json.dumps({'error': 'Missing userId'})}
        
        # 2. Update DynamoDB cleanly with camelCase keys matching React
        response = table.update_item(
            Key={'id': user_id},
            UpdateExpression='SET city = :c, alertsEnabled = :ae, emailEnable = :ee, textEnable = :te, alertFrequency = :af',
            ExpressionAttributeValues={
                ':c': body.get('city'),
                ':ae': body.get('alertsEnabled'),
                ':ee': body.get('emailEnable'),
                ':te': body.get('textEnable'),
                ':af': body.get('alertFrequency')
            },
            ReturnValues='ALL_NEW'
        )
        
        attributes = json.loads(json.dumps(response['Attributes'], default=str))
        
        return {'statusCode': 200, 'headers': HEADERS, 'body': json.dumps({'message': 'Success', 'data': attributes})}
        
    except Exception as e:
        print(f'Error updating user: {e}')
        return {'statusCode': 500, 'headers': HEADERS, 'body': json.dumps({'error': str(e)})}