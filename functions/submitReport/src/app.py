import json
import boto3
import base64
import uuid
import os
from datetime import datetime, timezone
from decimal import Decimal
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
reports_table = dynamodb.Table('weather-app-reports')
crowdsource_table = dynamodb.Table('weather-app-crowdsource')
users_table = dynamodb.Table('weather-app-table')

VALID_CONDITIONS = {'hotter', 'colder', 'raining', 'windy', 'fine'}
ANON_WEIGHT = Decimal('0.5')
DEFAULT_AUTH_WEIGHT = Decimal('0.75')

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'POST,OPTIONS',
    'Content-Type': 'application/json'
}

def response(status, body):
    return {'statusCode': status, 'headers': CORS_HEADERS, 'body': json.dumps(body)}

def decode_jwt_sub(token):
    """Extract sub from JWT payload. No signature verification — we use it only for weight lookup."""
    try:
        payload_b64 = token.split('.')[1]
        payload_b64 += '=' * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.b64decode(payload_b64))
        return payload.get('sub')
    except Exception:
        return None

def get_user_weight(user_id):
    try:
        item = users_table.get_item(Key={'id': user_id}).get('Item')
        if item:
            return Decimal(str(item.get('reliabilityScore', DEFAULT_AUTH_WEIGHT)))
    except Exception as e:
        print(f"Failed to get user reliability score: {e}")
    return DEFAULT_AUTH_WEIGHT

def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}

    try:
        body = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return response(400, {'error': 'Invalid JSON'})

    city = (body.get('city') or '').strip()
    condition = (body.get('condition') or '').strip().lower()
    # Accept date from client or default to today UTC
    date = (body.get('date') or '').strip() or datetime.now(timezone.utc).strftime('%Y-%m-%d')

    if not city:
        return response(400, {'error': 'Missing city'})
    if condition not in VALID_CONDITIONS:
        return response(400, {'error': f"Invalid condition. Must be one of: {', '.join(sorted(VALID_CONDITIONS))}"})

    # Determine reporter weight
    user_id = None
    auth_header = (event.get('headers') or {}).get('Authorization') or (event.get('headers') or {}).get('authorization')
    if auth_header and auth_header.startswith('Bearer '):
        user_id = decode_jwt_sub(auth_header[7:])

    weight = get_user_weight(user_id) if user_id else ANON_WEIGHT

    # Write individual report (used later for reliability scoring)
    report_id = str(uuid.uuid4())
    ttl = int(datetime.now(timezone.utc).timestamp()) + (30 * 24 * 60 * 60)  # 30-day TTL

    try:
        reports_table.put_item(Item={
            'city': city,
            'reportId': f"{date}#{report_id}",
            'userId': user_id,
            'condition': condition,
            'weight': weight,
            'date': date,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'ttl': ttl
        })
    except Exception as e:
        print(f"Failed to write report: {e}")
        return response(500, {'error': 'Failed to save report'})

    # Update running aggregate using ADD — safely initializes missing Number attributes to 0
    try:
        crowdsource_table.update_item(
            Key={'city': city, 'date': date},
            UpdateExpression='ADD #cond :w SET lastUpdated = :ts',
            ExpressionAttributeNames={'#cond': condition},
            ExpressionAttributeValues={
                ':w': weight,
                ':ts': datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        # Report is already saved — don't fail the whole request over the aggregate
        print(f"Failed to update aggregate (report was saved): {e}")

    return response(200, {'success': True, 'weight': float(weight)})
