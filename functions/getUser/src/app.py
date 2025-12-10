import boto3
import json

#Need function to update city, email/text preferences, alert frequency

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('weather-app-table')

def checkUser(user_id):
    response = table.get_item(
        Key={'id': user_id}
    )

    if 'Item' not in response:
        raise ValueError(f"User with id {user_id} not found.")
    
    userSettings = response['Item']
    return userSettings





#
def lambda_handler(event, context):

    query_params = event.get("queryStringParameters") or {}
    user_id = query_params.get("id")

    if not user_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing user id'})
        }
    
    try:
        user = checkUser(user_id)

        return {
        'statusCode': 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",  # need to update to specific origin
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
        },
        'body': json.dumps(user)
    }



    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
    