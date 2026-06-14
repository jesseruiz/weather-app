# Rain for Thee

A serverless weather alert web app. Enter any US city to get a 7-day forecast and alerts for extreme heat, high winds, or heavy rain. Signed-in users get a personalized forecast for their saved city and can configure email or SMS notifications.

## Architecture

```
Browser → CloudFront → S3 (React SPA)
                ↓
         API Gateway → Lambda (Python 3.11, ECR images)
                ↓
         DynamoDB  ·  SES  ·  SQS  ·  Cognito
```

**Frontend** — React 19 + Vite SPA, served from S3 via CloudFront. GitHub Actions deploys automatically on every push to `main`.

**Auth** — AWS Cognito User Pool. Sign-up requires a valid US city (geocoded at registration via the `PreSignUp` trigger). The frontend uses AWS Amplify UI components and passes a Cognito `idToken` as a Bearer token on all protected API calls.

**Backend** — Python 3.11 Lambda functions packaged as Docker images and stored in ECR. Each function is triggered independently (API Gateway, EventBridge, SQS, or Cognito).

**Database** — Two DynamoDB tables:
- `weather-app-table` — user profiles (PK: Cognito `sub`)
- `weather-app-cities` — weather cache (PK: city, SK: forecastType)

**Weather data** — [NWS API](https://api.weather.gov) (US only). Cities are geocoded to lat/long via `geopy` before querying NWS.

**Notifications** — SES for email. Alert conditions: heat > 102°F, wind > 25 mph, rain probability > 50%.

## Lambda Functions

| Function | Trigger | Purpose |
|---|---|---|
| `mainWeatherFunction` | API Gateway `GET /weather?city=` | Public forecast lookup; checks DynamoDB cache, falls back to NWS |
| `MyForecastFunction` | API Gateway `GET /weekly?id=` | Returns weekly forecast for user's saved city |
| `getUser` | API Gateway `GET /get_user?id=` | Fetch user profile |
| `updateUser` | API Gateway `POST /update_user` | Update user settings; geocodes city if changed |
| `getWeatherCards` | API Gateway `GET` | Full city list for public weather slider |
| `PostConfirmation` | Cognito Post-Confirmation | Creates user record in DynamoDB; seeds weather cache |
| `PreSignUp` | Cognito Pre-Sign-Up | Validates and geocodes `custom:City` attribute |
| `EnqueueCitiesFunction` | SQS `Weather-app-cities-queue` | Worker: fetches NWS data and writes city cache to DynamoDB |
| `citiesWeatherFunction` | EventBridge (scheduled) | Scans all cities and enqueues each to SQS for refresh |
| `sendNotificationsFunction` | SQS `Weather-Alerts` | Sends email alerts via SES |

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, React Router v7, AWS Amplify UI |
| Hosting | S3 + CloudFront |
| Auth | AWS Cognito |
| API | API Gateway (REST) |
| Compute | AWS Lambda (Python 3.11, Docker/ECR) |
| Database | DynamoDB |
| Messaging | SQS, SES |
| CI/CD | GitHub Actions |

## Local Development

### Prerequisites
- Node.js 18+
- AWS credentials configured locally (for Lambda testing scripts)

### Frontend

```bash
cd html
npm install
npm run dev       # dev server at http://localhost:5173
npm run build     # production build → html/dist/
npm run lint      # ESLint
npm run preview   # preview production build
```

The frontend talks to the live API Gateway endpoint — there is no local backend emulation. Cognito config is in `html/src/amplify-configure.js`.

### Lambda functions

Each function lives in `functions/<name>/src/`. Dependencies are in `requirements.txt`. Ad-hoc testing scripts are in `testing/` and run locally against AWS using your configured credentials.

## Deployment

### Frontend
Automatic — GitHub Actions deploys to S3 and invalidates the CloudFront cache on every push to `main`.

### Lambda functions
Manual. Each function must be built as a Docker image, pushed to ECR, and the Lambda updated:

```bash
# Example for one function
cd functions/mainWeatherFunction
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker build -t main-weather-function .
docker tag main-weather-function:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/main-weather-function:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/main-weather-function:latest
aws lambda update-function-code --function-name mainWeatherFunction --image-uri <account-id>.dkr.ecr.us-east-1.amazonaws.com/main-weather-function:latest
```

## Environment Variables

The following must be set in the Lambda console (not stored in code):

| Function | Variable | Description |
|---|---|---|
| `sendNotificationsFunction` | `SES_SENDER_EMAIL` | Verified SES sender address |
| `EnqueueCitiesFunction` | `CITIES_QUEUE_URL` | SQS queue URL for city refresh |
| `mainWeatherFunction` | `WIND_ALERT_THRESHOLD` | Wind alert threshold in mph (default: 25) |
| `mainWeatherFunction` | `RAIN_ALERT_THRESHOLD` | Rain alert threshold in % (default: 50) |
| `mainWeatherFunction` | `HEAT_ALERT_THRESHOLD` | Heat alert threshold in °F (default: 102) |

## API

Base URL: `https://raj8a28np4.execute-api.us-east-1.amazonaws.com`

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/weather?city=` | None | Public forecast + alerts for any US city |
| `GET` | `/weekly?id=` | Bearer token | Personalized forecast for user's saved city |
| `GET` | `/get_user?id=` | Bearer token | User profile |
| `POST` | `/update_user` | Bearer token | Update user settings |
| `GET` | `/getWeatherCards` | None | All cached city forecasts |
