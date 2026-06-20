import boto3
import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from collections import defaultdict
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb')
reports_table = dynamodb.Table('weather-app-reports')
crowdsource_table = dynamodb.Table('weather-app-crowdsource')
users_table = dynamodb.Table('weather-app-table')

SCORE_REWARD = Decimal('0.05')
SCORE_PENALTY = Decimal('0.10')
SCORE_MAX = Decimal('2.0')
SCORE_MIN = Decimal('0.25')
DEFAULT_SCORE = Decimal('0.75')
MAJORITY_THRESHOLD = Decimal('0.6')  # majority must be >60% of weighted votes to trigger scoring


def get_yesterday():
    return (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')


def scan_all(table, **kwargs):
    """Paginate through a full scan, returning all items."""
    items = []
    while True:
        result = table.scan(**kwargs)
        items.extend(result.get('Items', []))
        if 'LastEvaluatedKey' not in result:
            break
        kwargs['ExclusiveStartKey'] = result['LastEvaluatedKey']
    return items


def lambda_handler(event, context):
    yesterday = get_yesterday()
    print(f"closeReports: processing {yesterday}")

    # Pull all individual reports for yesterday
    reports = scan_all(reports_table, FilterExpression=Attr('date').eq(yesterday))
    print(f"Found {len(reports)} reports")

    if not reports:
        print("Nothing to process.")
        return {'statusCode': 200, 'body': 'No reports'}

    # Group reports by city
    by_city = defaultdict(list)
    for r in reports:
        by_city[r['city']].append(r)

    # Accumulate score deltas per user across all cities they reported in
    user_deltas = defaultdict(Decimal)

    for city, city_reports in by_city.items():
        # Weighted vote totals per condition
        totals = defaultdict(Decimal)
        for r in city_reports:
            totals[r['condition']] += Decimal(str(r.get('weight', '0.5')))

        total_weight = sum(totals.values())
        if total_weight == 0:
            continue

        top_condition = max(totals, key=lambda c: totals[c])
        top_share = totals[top_condition] / total_weight
        majority_clear = top_share >= MAJORITY_THRESHOLD

        # Mark aggregate as closed regardless of whether majority was clear
        try:
            crowdsource_table.update_item(
                Key={'city': city, 'date': yesterday},
                UpdateExpression='SET #s = :s',
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':s': 'closed'}
            )
        except Exception as e:
            print(f"Failed to close aggregate for {city}: {e}")

        if not majority_clear:
            print(f"{city}: no clear majority ({top_condition} at {float(top_share):.0%}) — skipping scoring")
            continue

        print(f"{city}: majority={top_condition} ({float(top_share):.0%}) — scoring {len(city_reports)} reports")

        for r in city_reports:
            user_id = r.get('userId')
            if not user_id:
                continue  # anonymous — no score to update
            if r['condition'] == top_condition:
                user_deltas[user_id] += SCORE_REWARD
            else:
                user_deltas[user_id] -= SCORE_PENALTY

    # Apply accumulated deltas to user records
    print(f"Updating scores for {len(user_deltas)} users")
    for user_id, delta in user_deltas.items():
        try:
            item = users_table.get_item(Key={'id': user_id}).get('Item', {})
            current = Decimal(str(item.get('reliabilityScore', DEFAULT_SCORE)))
            new_score = max(SCORE_MIN, min(SCORE_MAX, current + delta))

            users_table.update_item(
                Key={'id': user_id},
                UpdateExpression='SET reliabilityScore = :s',
                ExpressionAttributeValues={':s': new_score}
            )
            print(f"User {user_id[:8]}...: {float(current):.2f} → {float(new_score):.2f} ({float(delta):+.2f})")
        except Exception as e:
            print(f"Failed to update score for user {user_id}: {e}")

    return {
        'statusCode': 200,
        'body': f"Processed {len(reports)} reports across {len(by_city)} cities"
    }
