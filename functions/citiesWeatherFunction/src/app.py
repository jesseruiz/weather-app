import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('weather-app-cities')
sqs = boto3.client('sqs')

QUEUE_URL = os.environ['CITIES_QUEUE_URL']

def lambda_handler(event, context):
    try:
        response = table.scan(ProjectionExpression="city")
        cities = response.get('Items', [])

        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ProjectionExpression="city",
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            cities.extend(response.get('Items', []))

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
