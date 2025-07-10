# Usage and Cost Report API

A FastAPI-based REST API for querying usage and cost reports from a CSV file, with support for flexible filtering and tag extraction.

## Repository

**GitHub**: [https://github.com/AdarBahar/API-Sample](https://github.com/AdarBahar/API-Sample)

## Features
- **Comprehensive Filtering**: Query usage and cost data by account, subscription, database, plan type, date range, region, and custom tags
- **Flexible Parameters**: All query parameters are optional except `account_id` - use any combination to filter results
- **Structured Responses**: Returns data in a predictable format with `data` array and `total_rows` count
- **Configurable Row Limits**: Adjustable row limits (1-100) for testing purposes with default safety limit of 10 rows
- **Robust Validation**: Numeric-only validation for IDs, date format validation (YYYY-MM-DD), row limit validation
- **Dynamic Tag Support**: Extracts and filters by custom tags from CSV columns (key1:value, key2:value format)
- **Error Handling**: Returns structured JSON errors with clear messages and appropriate HTTP status codes
- **OpenAPI Documentation**: Interactive Swagger UI with enhanced column widths for better readability

## Requirements
- Python 3.10+
- pip (Python package manager)
- Recommended: virtualenv

## Setup
1. **Create and activate a virtual environment (optional but recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   For development (includes testing and code quality tools):
   ```bash
   pip install -r requirements-dev.txt
   ```
3. **Place your `cost_report.csv` file in the project root.**

## Running Locally
Start the API server with:
```bash
uvicorn app:app --reload --port 8090
```

Visit the interactive docs at: [http://127.0.0.1:8090/docs](http://127.0.0.1:8090/docs)

## API Usage
### Endpoint
```
GET /usage-cost-report
```

#### Query Parameters:
- `account_id`: **MANDATORY** - Account ID for the request (mandatory, numeric only)
- `subscription_id`: (Optional) Filter by subscription/cluster ID (numeric only)
- `database_id`: (Optional) Filter by database ID (numeric or null)
- `plan_type`: (Optional) Filter by plan type
- `start_date`: (Optional) Filter for usage starting on or after this date (YYYY-MM-DD)
- `end_date`: (Optional) Filter for usage ending on or before this date (YYYY-MM-DD)
- `region`: (Optional) Filter by region
- `tag1`: (Optional) Filter by tag1 value (key1:value)
- `tag2`: (Optional) Filter by tag2 value (key2:value)
- `limit`: (Optional) Maximum number of rows to return (default: 10, max: 100) - **TESTING ONLY**

📊 **Row Limit Control**:
- Default limit: **10 rows**
- Configurable limit: **1-100 rows** (for testing purposes)
- If your query returns more than the specified limit, a `RowLimitExceeded` error is returned.

⚠️ **Important**: The `limit` parameter is available for testing purposes only and should be removed in production environments.

#### Example Requests
**Basic request (default 10 rows):**
```bash
curl -X 'GET' \
  'http://127.0.0.1:8090/usage-cost-report?account_id=12345&plan_type=Pro&start_date=2024-10-01&end_date=2024-11-30&database_id=11415100&tag1=name15' \
  -H 'accept: application/json'
```

**Request with custom row limit (testing only):**
```bash
curl -X 'GET' \
  'http://127.0.0.1:8090/usage-cost-report?account_id=12345&plan_type=Pro&limit=50' \
  -H 'accept: application/json'
```

**Important**:
- The `account_id` parameter is mandatory and must be provided in every request. If omitted or empty, the API will return a 400 error with the message: `{"error": "account_id parameter is mandatory"}`.
- The API enforces a configurable row limit (default: 10, max: 100). If query results exceed this limit, the API returns a 413 error instead of truncated data. This prevents timeouts and large payloads.
- The `limit` parameter is for testing purposes only and should be removed in production environments.
- The `tag1` and `tag2` parameters search for values within the respective tag columns (key1:value and key2:value).
- Successful responses return a structured format with `data` (array of results) and `total_rows` (count of returned rows).

**Validation Rules**:
- **Numeric Parameters**: `account_id`, `subscription_id`, and `database_id` must contain only numeric characters (0-9). Invalid values will return a 400 error.
- **Date Parameters**: `start_date` and `end_date` must be in YYYY-MM-DD format. Invalid formats will return a 400 error.
- **Limit Parameter**: `limit` must be between 1 and 100. Invalid values will return a 422 validation error.

**Error Examples**:
- Invalid numeric (400): `{"error": "account_id must be numeric only"}`
- Invalid date (400): `{"error": "start_date must be in YYYY-MM-DD format"}`
- Row limit exceeded (413): `{"error": "RowLimitExceeded", "message": "The number of rows matching your request (25) exceeds the specified limit of 10. Please adjust your filters or increase the limit (max: 100)."}`

#### Response Format

**Successful Response (HTTP 200):**
```json
{
  "data": [
    {
      "subscription_id": "12345",
      "cluster_name": "example-cluster",
      "plan_type": "Pro",
      "region": "us-east-1",
      "start_date": "2024-10-01",
      "end_date": "2024-10-31",
      "charges": [
        {
          "charge_type": "Usage",
          "billing_unit_type": "large",
          "quantity": 2.0,
          "price_per_hour": 0.585,
          "hours": 720.0,
          "subtotal": 842.4,
          "total_cost": 842.4,
          "tags": {
            "key1:value": "name15:value15"
          }
        }
      ]
    }
  ],
  "total_rows": 1
}
```

**Error Response (HTTP 413 - Row Limit Exceeded):**
```json
{
  "error": "RowLimitExceeded",
  "message": "The number of rows matching your request (25) exceeds the specified limit of 10. Please adjust your filters or increase the limit (max: 100)."
}
```

## Deployment

### Production Considerations
⚠️ **Before deploying to production:**
1. **Remove the `limit` parameter** from the API endpoint - it's intended for testing only
2. **Set a fixed row limit** in the code (recommended: 10-50 rows depending on your use case)
3. **Review and adjust** the `ABSOLUTE_MAX_ROWS_LIMIT` constant based on your performance requirements
4. **Consider implementing** authentication and rate limiting for production use

### Deployment Platforms
- You can deploy this app to platforms like [Render.com](https://render.com), [Railway.app](https://railway.app), [Fly.io](https://fly.io), or any cloud provider that supports Python web apps.
- For quick sharing, you can use [ngrok](https://ngrok.com/) to expose your local server.

### Production Deployment Steps
1. Remove the `limit` parameter from the endpoint
2. Set environment variables for configuration
3. Use a production WSGI server like Gunicorn
4. Configure proper logging and monitoring
5. Set up SSL/TLS certificates

## Contact
For questions or support, please open an issue on the [GitHub repository](https://github.com/AdarBahar/API-Sample/issues).