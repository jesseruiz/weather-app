import json
from app import lambda_handler  # rename to match your file

# Simulate what SQS sends to Lambda
mock_event = {
    "Records": [
        {
            "body": json.dumps({
                "email": "jesseruiz321@aol.com",
                "city": "Seattle"
            })
        }
    ]
}

mock_context = {}  # Lambda context isn't used in your code

lambda_handler(mock_event, mock_context)