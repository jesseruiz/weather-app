import json
import boto3
from datetime import datetime, timezone, date as date_type
from decimal import Decimal
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
leaderboard_table = dynamodb.Table('weather-app-trivia-leaderboard')

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,OPTIONS',
    'Content-Type': 'application/json',
}

VALID_PERIODS = ('daily', 'weekly', 'monthly', 'yearly')


def response(status, body):
    return {
        'statusCode': status,
        'headers': CORS_HEADERS,
        'body': json.dumps(body, default=lambda o: int(o) if isinstance(o, Decimal) else o),
    }


def get_period_value(period, today):
    if period == 'daily':
        return today.strftime('%Y-%m-%d')
    if period == 'weekly':
        iso = today.isocalendar()
        return f"{iso[0]}-W{iso[1]:02d}"
    if period == 'monthly':
        return today.strftime('%Y-%m')
    return today.strftime('%Y')


def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}

    params = event.get('queryStringParameters') or {}
    period = params.get('period', 'daily')

    if period not in VALID_PERIODS:
        return response(400, {'error': f"period must be one of: {', '.join(VALID_PERIODS)}"})

    today = datetime.now(timezone.utc).date()
    period_value = get_period_value(period, today)

    result = leaderboard_table.query(
        KeyConditionExpression=Key('period').eq(period) & Key('periodKey').begins_with(period_value + '#'),
        Limit=10,
        ScanIndexForward=True,
    )

    entries = [
        {
            'rank': i + 1,
            'displayName': item['displayName'],
            'score': int(item['score']),
            'userId': item['userId'],
        }
        for i, item in enumerate(result.get('Items', []))
    ]

    return response(200, {
        'period': period,
        'periodValue': period_value,
        'leaderboard': entries,
    })
