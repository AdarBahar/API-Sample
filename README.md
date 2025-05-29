# Usage & Cost API

A FastAPI-based REST API for querying usage and cost reports from a CSV file, with support for flexible filtering and tag extraction.

## Features
- Query usage and cost data by subscription, plan type, date range, and region
- Supports any combination of query parameters (all optional)
- Returns detailed charge breakdowns, including dynamic tags (from columns in the format `key:value`)
- Handles missing or malformed data gracefully
- OpenAPI/Swagger documentation included

## Requirements
- Python 3.10+
- pip (Python package manager)
- Recommended: virtualenv

## Setup
1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd <repo-directory>
   ```
2. **Create and activate a virtual environment (optional but recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install fastapi uvicorn pandas numpy
   ```
4. **Place your `cost_report.csv` file in the project root.**

## Running Locally
Start the API server with:
```bash
uvicorn app:app --reload --port 8090
```

Visit the interactive docs at: [http://127.0.0.1:8090/docs](http://127.0.0.1:8090/docs)

## API Usage
### Endpoint
```
GET /api/v1/usage-report
```

#### Query Parameters (all optional, any combination):
- `subscription_id`: Filter by subscription/cluster ID
- `plan_type`: Filter by plan type
- `start_date`: Filter for usage starting on or after this date (format: YYYY-MM-DD)
- `end_date`: Filter for usage ending on or before this date (format: YYYY-MM-DD)
- `region`: Filter by region

#### Example Request
```bash
curl -X 'GET' \
  'http://127.0.0.1:8090/api/v1/usage-report?plan_type=Pro&start_date=2024-10-01&end_date=2024-11-30' \
  -H 'accept: application/json'
```

#### Response
- Returns a list of usage reports, each with detailed charge items.
- If any tag columns (in the format `key:value`) are present in the CSV, they will appear as a `tags` dictionary in the response for relevant charge items.

## Deployment
- You can deploy this app to platforms like [Render.com](https://render.com), [Railway.app](https://railway.app), [Fly.io](https://fly.io), or any cloud provider that supports Python web apps.
- For quick sharing, you can use [ngrok](https://ngrok.com/) to expose your local server.

## Contact
For questions or support, contact: [adar@bahar.co.il] 
