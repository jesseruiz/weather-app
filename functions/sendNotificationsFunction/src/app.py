import boto3
import json

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('weather-app-table')

def getUsers():
    try:
        response = table.scan(
            FilterExpression="alerts = :val",
            ExpressionAttributeValues={
                ":val": True
            }
        )

        items = response.get("Items", [])

        print(items)

    except Exception as e:
        print(f"Error with DynamoDB scan: {e}")


getUsers