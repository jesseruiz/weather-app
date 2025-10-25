import boto3

def lambda_handler(event, context):

    try:
        response = table.scan()
        items = response.get('Items', [])
    except Exception as e:
        print(f"Error scanning DynamoDB: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to fetch weather data"})
        }

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",  # or specific origin
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
        },
        "body": json.dumps(items, default=decimal_default)
    }