import boto3
import json

dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/745167176709/Weather-app-cities-queue'

def lambda_handler(event, context):
    table = dynamodb.Table('weather-app-cities')
    
    try:
        # 1. Scan the database to get all tracked cities
        response = table.scan(ProjectionExpression="city")
        cities = response.get('Items', [])
        
        # Handle pagination if you have more than 1MB of cities
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ProjectionExpression="city",
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            cities.extend(response.get('Items', []))

        # 2. Send each city directly into the SQS Queue
        for item in cities:
            city_name = item.get('city')
            if city_name:
                sqs.send_message(
                    QueueUrl=QUEUE_URL,
                    MessageBody=json.dumps({'city': city_name})
                )
                print(f"Dispatched {city_name} to SQS.")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': f'Successfully queued {len(cities)} cities.'})
        }
        
    except Exception as e:
        print(f"Error scanning cities: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}