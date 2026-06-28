import json
import base64
import hashlib
import random
import boto3
from datetime import datetime
from zoneinfo import ZoneInfo
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
questions_table = dynamodb.Table('weather-app-trivia-questions')
scores_table = dynamodb.Table('weather-app-trivia-scores')

PACIFIC = ZoneInfo('America/Los_Angeles')
POOL_SIZE = 25
QUESTIONS_PER_USER = 5

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,OPTIONS',
    'Content-Type': 'application/json',
}


def response(status, body):
    return {'statusCode': status, 'headers': CORS_HEADERS, 'body': json.dumps(body)}


def decode_jwt(token):
    try:
        payload_b64 = token.split('.')[1]
        payload_b64 += '=' * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.b64decode(payload_b64))
        return payload.get('sub')
    except Exception:
        return None


def get_assigned_question_ids(user_id, date):
    seed = int(hashlib.sha256(f"{user_id}{date}".encode()).hexdigest(), 16)
    rng = random.Random(seed)
    selected = rng.sample(range(1, POOL_SIZE + 1), QUESTIONS_PER_USER)
    return {f"q{n:02d}" for n in selected}


def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}

    today = datetime.now(PACIFIC).strftime('%Y-%m-%d')

    user_id = None
    auth_header = (event.get('headers') or {}).get('Authorization') or \
                  (event.get('headers') or {}).get('authorization')
    if auth_header and auth_header.startswith('Bearer '):
        user_id = decode_jwt(auth_header[7:])

    # Check if this user already completed today's trivia
    if user_id:
        score_record = scores_table.get_item(Key={'userId': user_id, 'date': today}).get('Item')
        if score_record and 'totalScore' in score_record:
            return response(200, {
                'completed': True,
                'totalScore': int(score_record['totalScore']),
                'message': "You've already played today! New questions drop at midnight Pacific time.",
            })

    result = questions_table.query(
        KeyConditionExpression=Key('date').eq(today)
    )
    items = result.get('Items', [])
    if not items:
        return response(404, {'error': 'No questions available today. Check back soon!'})

    if user_id:
        assigned_ids = get_assigned_question_ids(user_id, today)
    else:
        selected = random.sample(range(1, POOL_SIZE + 1), QUESTIONS_PER_USER)
        assigned_ids = {f"q{n:02d}" for n in selected}

    filtered = sorted(
        [item for item in items if item['questionId'] in assigned_ids],
        key=lambda x: x['questionId'],
    )

    questions = [
        {
            'questionId': item['questionId'],
            'question': item['question'],
            'choices': item['choices'],
            'category': item['category'],
        }
        for item in filtered
    ]

    return response(200, {'date': today, 'questions': questions})
