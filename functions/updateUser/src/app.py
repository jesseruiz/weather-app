import boto3
import json

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('weather-app-table')

def checkUserSub(user_id):
    response = table.get_item(
        Key={'id': user_id}
    )

    if 'Item' not in response:
        raise ValueError(f"User with id {user_id} not found.")

    return response['Item']['subscription']

def lambda_handler(event, context):
    query_params = event.get("queryStringParameters") or {}
    user_id = query_params.get("id")

    if not user_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing user id'})
        }

    try:
        subscription = checkUserSub(user_id)

        if subscription == 'basic':
            new_subscription = 'premium'
        else:
            new_subscription = 'basic'

        table.update_item(
            Key={'id': user_id},
            UpdateExpression='SET subscription = :val1',
            ExpressionAttributeValues={':val1': new_subscription}
        )

        return {
            'statusCode': 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",  # or specific origin
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
            },
            'body': json.dumps({'message': f'User {user_id} subscription changed to {new_subscription}'})
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
