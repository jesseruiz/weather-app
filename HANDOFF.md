# Project Handoff — Rain for Thee / On A Heater!

> This document supplements `CLAUDE.md` (which covers base architecture). Read CLAUDE.md first, then this file for current operational state, trivia system details, deployment instructions, and known gotchas.

---

## AWS Account Info

| Item | Value |
|---|---|
| AWS CLI profile | `jesse-personal` |
| Account ID | `745167176709` |
| Region | `us-east-1` |
| API Gateway ID | `raj8a28np4` (HTTP API v2, **not** REST API v1) |
| API base URL | `https://raj8a28np4.execute-api.us-east-1.amazonaws.com` |
| S3 bucket (frontend) | `weatheralertsapp` |
| Cognito User Pool | `us-east-1_0c1i9TA7N` |

Always use `--profile jesse-personal --region us-east-1` with AWS CLI commands.

---

## Current State (as of 2026-06-30)

Everything is live and working:

- **Frontend** — deployed to S3/CloudFront via GitHub Actions on push to `main`
- **Trivia game** — fully live (all 4 Lambdas deployed, questions generating daily)
- **Leaderboard** — daily/weekly/monthly/yearly, live at `/Leaderboard`
- **Accessibility** — WCAG 2.1 AA audit complete

---

## All DynamoDB Tables

| Table | PK | SK | Purpose |
|---|---|---|---|
| `weather-app-table` | `id` (Cognito sub) | — | User profiles, alert settings |
| `weather-app-cities` | `city` | `forecastType` (always `"weekly"`) | Weather cache |
| `weather-app-reports` | `city` | `reportId` | Crowdsource weather reports (TTL enabled) |
| `weather-app-crowdsource` | `city` | `date` | Aggregated crowdsource votes per city/day |
| `weather-app-trivia-questions` | `date` (YYYY-MM-DD Pacific) | `questionId` (q01–q25) | Daily trivia questions |
| `weather-app-trivia-scores` | `userId` | `date` | Per-user game records and period bests |
| `weather-app-trivia-leaderboard` | `period` | `periodKey` | Pre-aggregated leaderboard entries |

### `weather-app-trivia-scores` SK patterns
- `YYYY-MM-DD` — daily game record (has `answers` map + `totalScore`)
- `best#weekly#YYYY-Www` — user's best weekly score tracker
- `best#monthly#YYYY-MM` — user's best monthly score tracker
- `best#yearly#YYYY` — user's best yearly score tracker

### `weather-app-trivia-leaderboard` periodKey format
```
{period_value}#{inverted_score_padded}#{unix_timestamp}#{userId}
```
- `inverted_score = int(round((751 - leaderboard_score) * 100000))`, zero-padded to 8 digits
- Ascending sort naturally returns highest scores first
- Timestamp breaks ties — earlier finisher ranks higher

---

## All API Gateway Routes

| Method | Path | Lambda | Auth |
|---|---|---|---|
| GET | `/weather` | `mainWeatherFunction` | None |
| GET | `/weekly` | `MyForecastFunction` | Bearer token |
| GET | `/get_user` | `getUser` | Bearer token |
| POST | `/update_user` | `updateUser` | Bearer token |
| GET | `/cards` | `getWeatherCards` | None |
| POST | `/report` | `submitReport` | None (optional) |
| GET | `/trivia/questions` | `getTriviaQuestions` | None (optional Bearer) |
| POST | `/trivia/submit` | `submitTriviaAnswer` | None (optional Bearer) |
| GET | `/trivia/leaderboard` | `getTriviaLeaderboard` | None |

---

## Trivia System — Full Details

### How it works
1. **`generateDailyTrivia`** runs on an EventBridge schedule (early AM Pacific). Calls Claude Haiku 4.5 asking for 30 questions, stores the first 25 in DynamoDB keyed by today's Pacific date. Idempotent — skips if `q01` already exists for today.

2. **`getTriviaQuestions`** (`GET /trivia/questions`):
   - Auth users: returns a deterministic 5-of-25 subset based on `sha256(userId + date)` seed — same user always gets same 5 questions for a given day
   - Guests: returns a random 5
   - If user already has `totalScore` in scores table → returns `{completed: true}` instead of questions
   - Correct answers are **never** returned to the client

3. **`submitTriviaAnswer`** (`POST /trivia/submit`):
   - Body: `{ questionId, answer (0–3), timeRemainingMs }`
   - Derives today's Pacific date server-side — client does not send date
   - Validates question is in user's assigned set (auth users only)
   - Scoring: 100 pts + `int((timeRemainingMs / 15000) * 50)` speed bonus per correct answer
   - On 5th answer: writes `totalScore` to scores table, triggers leaderboard write

4. **`getTriviaLeaderboard`** (`GET /trivia/leaderboard?period=daily|weekly|monthly|yearly`):
   - Returns top 10 for the current period
   - Daily: today's scores
   - Weekly/Monthly/Yearly: each user's **best single-day score** for that period

### Scoring / tiebreaker
- Per-question points: integer (shown to user)
- Leaderboard sort score: `total_int + (sum_of_all_timeRemainingMs / 75000)` — adds fractional [0,1) to make identical integer scores effectively impossible to tie
- Secondary tiebreaker: Unix timestamp in periodKey — earliest finisher wins

### Daily lock
- Auth users: locked by presence of `totalScore` in `weather-app-trivia-scores`
- Guests: locked by `localStorage.getItem('trivia_played')` — `{date, score}` keyed to server-returned Pacific date

---

## Lambda Deployment (Manual Process)

All Lambdas are Docker/ECR image-based. There is no CI for Lambda — deploy manually when code changes.

```bash
# From the function directory, e.g. functions/submitTriviaAnswer/

# 1. Authenticate ECR
aws ecr get-login-password --region us-east-1 --profile jesse-personal \
  | docker login --username AWS --password-stdin \
    745167176709.dkr.ecr.us-east-1.amazonaws.com

# 2. Build image
docker build -t <function-name> .

# 3. Tag
docker tag <function-name>:latest \
  745167176709.dkr.ecr.us-east-1.amazonaws.com/<ecr-repo-name>:latest

# 4. Push
docker push 745167176709.dkr.ecr.us-east-1.amazonaws.com/<ecr-repo-name>:latest

# 5. Update Lambda to use new image
aws lambda update-function-code \
  --function-name <function-name> \
  --image-uri 745167176709.dkr.ecr.us-east-1.amazonaws.com/<ecr-repo-name>:latest \
  --region us-east-1 --profile jesse-personal
```

### Trivia Lambda names and ECR repos
Check ECR for exact repo names:
```bash
aws ecr describe-repositories --region us-east-1 --profile jesse-personal \
  --query 'repositories[].repositoryName'
```

### IAM gotcha
When creating a new Lambda, the auto-created role only gets CloudWatch Logs permissions. **DynamoDB permissions must be added manually.** Each trivia Lambda needs at minimum:
- `dynamodb:Query` and `dynamodb:GetItem` on its tables (getTriviaQuestions, getTriviaLeaderboard)
- `dynamodb:UpdateItem`, `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:DeleteItem` (submitTriviaAnswer — needs all 3 trivia tables)
- `dynamodb:PutItem`, `dynamodb:BatchWriteItem` (generateDailyTrivia)
- `ANTHROPIC_API_KEY` env var set on `generateDailyTrivia`

---

## Known Gotchas

### API Gateway is HTTP API v2, not REST API
Use `aws apigatewayv2` CLI commands, not `aws apigateway`. The event format in Lambdas uses v2 payload format — `event['requestContext']['http']['method']` not `event['httpMethod']`. The current Lambda code checks both for OPTIONS handling but be aware when writing new functions.

### `submitTriviaAnswer` — no `date` in request body
The Lambda derives the Pacific date server-side. Do NOT send a `date` field from the client. An older deployed version required it — if you ever see `{"error": "Missing date"}` the wrong image is deployed.

### `generateDailyTrivia` — ask for 30, store 25
Claude Haiku sometimes returns 24 instead of 25 when asked for exactly 25. The prompt asks for 30 and the Lambda takes the first 25. Do not change this back.

### Leaderboard old entries
Any leaderboard entries written before the scoring fix (2026-06-30) are in the old key format (`{period_value}#{inverted5digit}#{userId}`) and won't sort correctly alongside new entries. Safe to truncate `weather-app-trivia-leaderboard` table for a clean slate — entries rebuild as users play.

### `zoneinfo` and Pacific time
All trivia Lambdas use `ZoneInfo('America/Los_Angeles')` for Pacific date. The Docker base image must have `tzdata` installed, or this raises `ZoneInfoNotFoundError`. Check `requirements.txt` includes `tzdata` if seeing timezone errors.

---

## Frontend Routes

| Path | Component | Auth |
|---|---|---|
| `/` | Home | Public |
| `/Trivia` | Trivia | Public (scores only for auth) |
| `/Leaderboard` | Leaderboard | Public |
| `/MyForecast` | MyForecastWrapper | Protected |
| `/Dashboard` | Dashboard | Protected |
| `/Manage-Alerts` | ManageAlerts | Protected |
| `/Update-Password` | UpdatePassword | Protected |
| `/Contact` | Contact | Public |
| `/login` | LoginPage | Public |

`api.js` exports `API_BASE` — the API Gateway base URL.

---

## Future Work Queue

These were flagged by the user as future priorities. Do not start without being asked.

1. **Deployment test flows** — smoke tests / integration checks post-Lambda-deploy
2. **Metrics, logging, dashboards** — CloudWatch or lightweight observability, useful dashboards
3. **Data tracking compliance** — GDPR/CCPA review of DynamoDB storage, localStorage, Cognito data

---

## Repo

`github.com/jesseruiz/weather-app` — public repo. All secrets in GitHub Actions secrets and Lambda env vars (never in code).
