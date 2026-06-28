import json
import boto3
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import anthropic

dynamodb = boto3.resource('dynamodb')
questions_table = dynamodb.Table('weather-app-trivia-questions')

PACIFIC = ZoneInfo('America/Los_Angeles')

QUESTION_PROMPT = """Generate exactly 25 multiple-choice weather trivia questions. Cover a mix of: historical weather events, extreme weather records, meteorology concepts, and famous storms/disasters.

Return ONLY a JSON array with no markdown, no explanation, just the raw array. Each object must have:
- "question": the trivia question (string)
- "choices": exactly 4 answer options (array of strings, each concise and distinct)
- "correctAnswer": index of the correct choice (integer 0-3)
- "explanation": 1-2 sentence explanation of the correct answer (string)
- "category": one of "Weather Records", "Historical Events", "Meteorology", "Storms & Disasters"

Make questions interesting, factual, and varied in difficulty. Do not repeat questions from previous days."""


def lambda_handler(event, context):
    today = datetime.now(PACIFIC).strftime('%Y-%m-%d')

    existing = questions_table.get_item(Key={'date': today, 'questionId': 'q01'}).get('Item')
    if existing:
        print(f"Questions already exist for {today}, skipping.")
        return {'statusCode': 200, 'body': 'Already generated'}

    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

    message = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=8192,
        messages=[{'role': 'user', 'content': QUESTION_PROMPT}]
    )

    raw = message.content[0].text.strip()
    questions = json.loads(raw)

    if len(questions) != 25:
        raise ValueError(f"Expected 25 questions, got {len(questions)}")

    with questions_table.batch_writer() as batch:
        for i, q in enumerate(questions, 1):
            batch.put_item(Item={
                'date': today,
                'questionId': f'q{i:02d}',
                'question': q['question'],
                'choices': q['choices'],
                'correctAnswer': int(q['correctAnswer']),
                'explanation': q['explanation'],
                'category': q['category'],
            })

    print(f"Stored 25 questions for {today}")
    return {'statusCode': 200, 'body': f'Generated 25 questions for {today}'}
