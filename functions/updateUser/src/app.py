import json
import boto3


#Need function to update city, email/text preferences, alert frequency

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('weather-app-table')

def lambda_handler(event, context):
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',  # Update with your domain in production
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS',
        'Content-Type': 'application/json'
    }
    
    # Handle preflight OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # Parse the request body
        body = json.loads(event['body'])
        
        city = body.get('city')
        alerts = body.get('alertsEnabled')
        alerts_email = body.get('emailEnable')
        alerts_text = body.get('textEnable')
        alert_frequency = body.get('alertFrequency')
        user_id = body.get('userId')
        
        # Validate required fields
        if not user_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Missing required field: userId'
                })
            }
        
        # Update the item in DynamoDB
        response = table.update_item(
            Key={
                'id': user_id
            },
            UpdateExpression='SET city = :city, alerts = :alerts, alerts_email = :alerts_email, alerts_text = :alerts_text, alert_frequency = :alert_frequency',
            ExpressionAttributeValues={
                ':city': city,
                ':alerts': alerts,
                ':alerts_email': alerts_email,
                ':alerts_text': alerts_text,
                ':alert_frequency': alert_frequency
            },
            ReturnValues='ALL_NEW'
        )
        
        # Convert Decimal types to float for JSON serialization
        attributes = json.loads(json.dumps(response['Attributes'], default=str))
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'User settings updated successfully',
                'data': attributes
            })
        }
        
    except KeyError as e:
        print(f'Missing key in event: {e}')
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'error': 'Invalid request format',
                'details': str(e)
            })
        }
        
    except Exception as e:
        print(f'Error updating user: {e}')
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Failed to update user settings',
                'details': str(e)
            })
        }