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
MAX_POSSIBLE_SCORE = 751  # 5*150 theoretical max + 1 ceiling for inverted key math
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


def make_period_key(period_value, leaderboard_score, completed_ts, user_id):
    # Invert score so ascending sort returns highest scores first.
    # Precision: 5 decimal places. Zero-pad to 8 digits (max 75,100,000).
    inverted_int = int(round((MAX_POSSIBLE_SCORE - leaderboard_score) * 100000))
    inverted = str(inverted_int).zfill(8)
    # Include Unix timestamp (10 digits) so ties go to earliest finisher.
    ts_str = str(completed_ts).zfill(10)
    return f"{period_value}#{inverted}#{ts_str}#{user_id}"


def write_leaderboard(user_id, display_name, total_int, leaderboard_score, date_str, completed_ts):
    """
    daily   — always write (one game per day, enforced upstream).
    weekly/monthly/yearly — write only if this is the user's best single-day
                            score for that period; delete the previous entry
                            if we're displacing it.
    """
    period_values = get_period_values(date_str)
    completed_at = datetime.now(PACIFIC).isoformat()
    lb_score_decimal = Decimal(str(round(leaderboard_score, 5)))

    for period, period_value in period_values.items():
        period_key = make_period_key(period_value, leaderboard_score, completed_ts, user_id)

        if period == 'daily':
            leaderboard_table.put_item(Item={
                'period': period,
                'periodKey': period_key,
                'score': total_int,
                'userId': user_id,
                'displayName': display_name,
                'completedAt': completed_at,
            })
        else:
            # Check the user's stored best for this period
            best_sk = f"best#{period}#{period_value}"
            existing = scores_table.get_item(
                Key={'userId': user_id, 'date': best_sk}
            ).get('Item')

            current_best = float(existing['leaderboardScore']) if existing else -1

            if leaderboard_score > current_best:
                # Remove the old leaderboard entry if one exists
                if existing and existing.get('leaderboardKey'):
                    try:
                        leaderboard_table.delete_item(Key={
                            'period': period,
                            'periodKey': existing['leaderboardKey'],
                        })
                    except Exception as e:
                        print(f"Failed to delete old leaderboard entry: {e}")

                # Write new leaderboard entry
                leaderboard_table.put_item(Item={
                    'period': period,
                    'periodKey': period_key,
                    'score': total_int,
                    'userId': user_id,
                    'displayName': display_name,
                    'completedAt': completed_at,
                })

                # Record this as the new best for this period
                scores_table.put_item(Item={
                    'userId': user_id,
                    'date': best_sk,
                    'leaderboardScore': lb_score_decimal,
                    'leaderboardKey': period_key,
                    'gameDate': date_str,
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
        score_record = scores_table.get_item(Key={'userId': user_id, 'date': today}).get('Item')
        if score_record and 'totalScore' in score_record:
            return response(403, {'error': "You have already completed today's trivia."})

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
                total_int = sum(int(a['score']) for a in answers.values())

                # Fractional tiebreaker: cumulative raw time remaining, normalized to [0,1)
                # Makes identical integer scores essentially impossible to tie.
                total_time_remaining = sum(int(a.get('timeRemainingMs', 0)) for a in answers.values())
                tiebreaker = total_time_remaining / (TOTAL_QUESTIONS * TIMER_MS)
                leaderboard_score = total_int + tiebreaker

                completed_ts = int(datetime.now(PACIFIC).timestamp())

                scores_table.update_item(
                    Key={'userId': user_id, 'date': today},
                    UpdateExpression='SET totalScore = :ts',
                    ExpressionAttributeValues={':ts': total_int},
                )
                write_leaderboard(user_id, display_name, total_int, leaderboard_score, today, completed_ts)

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
