import json
import base64
import hashlib
import random
import re
import boto3
from datetime import datetime, date as date_type
from zoneinfo import ZoneInfo
from decimal import Decimal
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
questions_table = dynamodb.Table('weather-app-trivia-questions')
scores_table = dynamodb.Table('weather-app-trivia-scores')
leaderboard_table = dynamodb.Table('weather-app-trivia-leaderboard')

PACIFIC = ZoneInfo('America/Los_Angeles')
POOL_SIZE = 25
TOTAL_QUESTIONS = 5
TIMER_MS = 15000
QUESTION_ID_RE = re.compile(r'^q(0[1-9]|1[0-9]|2[0-5])$')  # q01–q25

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'POST,OPTIONS',
    'Content-Type': 'application/json',
}


def response(status, body):
    return {'statusCode': status, 'headers': CORS_HEADERS, 'body': json.dumps(body)}


def decode_jwt(token):
    try:
        payload_b64 = token.split('.')[1]
        payload_b64 += '=' * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.b64decode(payload_b64))
        return payload.get('sub'), payload.get('email', '')
    except Exception:
        return None, ''


def get_assigned_question_ids(user_id, date):
    seed = int(hashlib.sha256(f"{user_id}{date}".encode()).hexdigest(), 16)
    rng = random.Random(seed)
    selected = rng.sample(range(1, POOL_SIZE + 1), TOTAL_QUESTIONS)
    return {f"q{n:02d}" for n in selected}


def get_period_values(date_str):
    d = date_type.fromisoformat(date_str)
    iso = d.isocalendar()
    return {
        'daily': date_str,
        'weekly': f"{iso[0]}-W{iso[1]:02d}",
        'monthly': date_str[:7],
        'yearly': date_str[:4],
    }


def write_leaderboard(user_id, display_name, score, date_str):
    period_values = get_period_values(date_str)
    completed_at = datetime.now(PACIFIC).isoformat()
    inverted = str(99999 - score).zfill(5)

    for period, period_value in period_values.items():
        period_key = f"{period_value}#{inverted}#{user_id}"
        leaderboard_table.put_item(Item={
            'period': period,
            'periodKey': period_key,
            'score': score,
            'userId': user_id,
            'displayName': display_name,
            'completedAt': completed_at,
        })


def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}

    try:
        body = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return response(400, {'error': 'Invalid JSON'})

    # Server-side date in Pacific time — client cannot fake a different day
    today = datetime.now(PACIFIC).strftime('%Y-%m-%d')

    question_id = (body.get('questionId') or '').strip()
    answer = body.get('answer')
    time_remaining_ms = body.get('timeRemainingMs', 0)

    if not QUESTION_ID_RE.match(question_id):
        return response(400, {'error': 'questionId must be q01–q25'})
    if not isinstance(answer, int) or answer not in (0, 1, 2, 3):
        return response(400, {'error': 'answer must be an integer 0–3'})
    if not isinstance(time_remaining_ms, (int, float)):
        time_remaining_ms = 0
    time_remaining_ms = max(0, min(int(time_remaining_ms), TIMER_MS))

    # Optional auth
    user_id = None
    display_name = 'Anonymous'
    auth_header = (event.get('headers') or {}).get('Authorization') or \
                  (event.get('headers') or {}).get('authorization')
    if auth_header and auth_header.startswith('Bearer '):
        user_id, email = decode_jwt(auth_header[7:])
        if user_id and email:
            display_name = email.split('@')[0]

    if user_id:
        # Reject if already completed today
        score_record = scores_table.get_item(Key={'userId': user_id, 'date': today}).get('Item')
        if score_record and 'totalScore' in score_record:
            return response(403, {'error': 'You have already completed today\'s trivia.'})

        # Validate the question belongs to this user's assigned set
        assigned = get_assigned_question_ids(user_id, today)
        if question_id not in assigned:
            return response(403, {'error': 'This question was not assigned to you today.'})

    question = questions_table.get_item(Key={'date': today, 'questionId': question_id}).get('Item')
    if not question:
        return response(404, {'error': 'Question not found for today.'})

    correct_answer = int(question['correctAnswer'])
    is_correct = answer == correct_answer

    if is_correct:
        speed_bonus = int((time_remaining_ms / TIMER_MS) * 50)
        points = 100 + speed_bonus
    else:
        points = 0

    if user_id:
        answer_data = {
            'correct': is_correct,
            'score': points,
            'timeRemainingMs': time_remaining_ms,
        }
        try:
            result = scores_table.update_item(
                Key={'userId': user_id, 'date': today},
                UpdateExpression='SET answers = if_not_exists(answers, :empty), answers.#qid = :ans',
                ConditionExpression='attribute_not_exists(answers.#qid)',
                ExpressionAttributeNames={'#qid': question_id},
                ExpressionAttributeValues={':empty': {}, ':ans': answer_data},
                ReturnValues='ALL_NEW',
            )
            updated = result.get('Attributes', {})
            answers = updated.get('answers', {})

            if len(answers) == TOTAL_QUESTIONS:
                total_score = sum(int(a['score']) for a in answers.values())
                scores_table.update_item(
                    Key={'userId': user_id, 'date': today},
                    UpdateExpression='SET totalScore = :ts',
                    ExpressionAttributeValues={':ts': total_score},
                )
                write_leaderboard(user_id, display_name, total_score, today)

        except ClientError as e:
            if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
                print(f"DynamoDB error: {e}")
                return response(500, {'error': 'Failed to save answer'})

    return response(200, {
        'correct': is_correct,
        'correctAnswer': correct_answer,
        'explanation': question['explanation'],
        'pointsEarned': points,
    })
