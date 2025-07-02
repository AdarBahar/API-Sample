# uvicorn app:app --reload --port 8090
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
import pandas as pd
import numpy as np
from fastapi.responses import JSONResponse, HTMLResponse
import os
import math
import re
from datetime import datetime

app = FastAPI(
    title="Usage and Cost Report API",
    version="1.0.0",
    description="""
API to retrieve usage and cost reports for your account.
All query parameters are optional except `account_id`.
Results are ordered by `start_date` (newest to oldest).

⚠️ The API enforces an internal maximum of **10 rows**.
If your query returns more than this limit, a `RowLimitExceeded` error is returned.
    """,
    docs_url=None,
    redoc_url=None
)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
        <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
        <title>{app.title} - Swagger UI</title>
        <style>
            /* Custom CSS to make Name and Type columns wider */
            .swagger-ui .parameters-col_name {{
                width: 25% !important;
                min-width: 200px !important;
            }}
            .swagger-ui .parameters-col_description {{
                width: 55% !important;
            }}
            .swagger-ui .parameter__name {{
                width: 200px !important;
                min-width: 200px !important;
                flex: 0 0 200px !important;
            }}
            .swagger-ui .parameter__type {{
                width: 120px !important;
                min-width: 120px !important;
                flex: 0 0 120px !important;
            }}
            .swagger-ui .parameter__description {{
                flex: 1 !important;
            }}
            .swagger-ui .parameters .parameter {{
                display: flex !important;
                align-items: flex-start !important;
            }}
            .swagger-ui table thead tr th {{
                min-width: 150px !important;
            }}
            .swagger-ui table thead tr th:first-child {{
                min-width: 200px !important;
            }}
            .swagger-ui table thead tr th:nth-child(2) {{
                min-width: 120px !important;
            }}
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
        const ui = SwaggerUIBundle({{
            url: '/openapi.json',
            dom_id: '#swagger-ui',
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.presets.standalone
            ],
            defaultModelsExpandDepth: 1,
            defaultModelExpandDepth: 1,
            docExpansion: "list",
            filter: true,
            showRequestHeaders: true,
            showCommonExtensions: true,
            showExtensions: true
        }})
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{app.title} - ReDoc</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body {{
                margin: 0;
                padding: 0;
            }}
        </style>
    </head>
    <body>
        <redoc spec-url='/openapi.json'></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

CSV_FILE = "cost_report.csv"
MAX_ROWS_LIMIT = 10  # Internal maximum rows limit

def load_dataframe():
    try:
        if not os.path.exists(CSV_FILE):
            raise FileNotFoundError(f"CSV file '{CSV_FILE}' not found.")
        df = pd.read_csv(CSV_FILE)
        print("CSV columns:", df.columns.tolist())  # Debug print
        df.replace({np.inf: None, -np.inf: None}, inplace=True)
        df = df.where(pd.notnull(df), None)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load CSV: {e}")

df = None
try:
    df = load_dataframe()
except Exception as e:
    df = None
    print(e)

class ChargeItem(BaseModel):
    charge_type: Optional[str] = None
    billing_unit_type: Optional[str] = None
    quantity: Optional[float] = None
    price_per_hour: Optional[float] = None
    hours: Optional[float] = None
    subtotal: Optional[float] = None
    discount: Optional[float] = None
    total_cost: Optional[float] = None
    tags: Optional[Dict[str, str]] = None

class UsageReport(BaseModel):
    subscription_id: str
    cluster_name: str
    plan_type: str
    region: str
    start_date: str
    end_date: str
    charges: List[ChargeItem]

class UsageReportResponse(BaseModel):
    data: List[UsageReport]
    total_rows: int

def validate_numeric(value, param_name):
    """Validate that a parameter contains only numeric characters"""
    if value is None:
        return True
    if not re.match(r'^\d+$', str(value).strip()):
        return False
    return True

def validate_date(date_str, param_name):
    """Validate date format YYYY-MM-DD"""
    if date_str is None:
        return True
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def clean_nans(obj):
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, list):
        return [clean_nans(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: clean_nans(v) for k, v in obj.items()}
    return obj

@app.get("/usage-cost-report", response_model=UsageReportResponse)
def get_usage_report(
    account_id: Optional[str] = Query(None, description="Account ID for the request (mandatory, numeric only). Testing: 12345"),
    subscription_id: Optional[str] = Query(None, description="Filter by subscription/cluster ID (numeric only)."),
    database_id: Optional[str] = Query(None, description="Filter by database ID (numeric or null)."),
    plan_type: Optional[str] = Query(None, description="Filter by plan type."),
    start_date: Optional[str] = Query(None, description="Filter for usage starting on or after this date (YYYY-MM-DD)."),
    end_date: Optional[str] = Query(None, description="Filter for usage ending on or before this date (YYYY-MM-DD)."),
    region: Optional[str] = Query(None, description="Filter by region."),
    tag1: Optional[str] = Query(None, description="Filter by tag1 value (key1:value)."),
    tag2: Optional[str] = Query(None, description="Filter by tag2 value (key2:value).")
):
    """Get usage and cost report.

    Retrieves usage and cost data for the specified account.
    All query parameters are optional except `account_id`, which is mandatory.
    You may use any combination of the optional parameters to filter results.

    The API enforces an internal maximum of **10 rows**.
    If the number of matching rows exceeds this limit, a `RowLimitExceeded` error is returned.
    Results are ordered by `start_date` (newest to oldest).

    Parameters:
    - `account_id`: Account ID for the request (mandatory, numeric only).
    - `subscription_id`: Filter by subscription/cluster ID (numeric only).
    - `database_id`: Filter by database ID (numeric or null).
    - `plan_type`: Filter by plan type.
    - `start_date`: Filter for usage starting on or after this date (YYYY-MM-DD).
    - `end_date`: Filter for usage ending on or before this date (YYYY-MM-DD).
    - `region`: Filter by region.
    - `tag1`: Filter by tag1 value (key1:value).
    - `tag2`: Filter by tag2 value (key2:value).

    Responses:
    - 200: Successful usage and cost report retrieval (up to 10 rows).
    - 400: Bad request, validation failed (e.g. invalid date format).
    - 413: RowLimitExceeded — the number of rows matching the request exceeds the internal limit of 10.
    """
    try:
        # Validate account_id parameter
        if account_id is None or account_id.strip() == "":
            return JSONResponse(status_code=400, content={"error": "account_id parameter is mandatory"})

        # Validate numeric parameters
        if not validate_numeric(account_id, "account_id"):
            return JSONResponse(status_code=400, content={"error": "account_id must be numeric only"})

        if subscription_id and not validate_numeric(subscription_id, "subscription_id"):
            return JSONResponse(status_code=400, content={"error": "subscription_id must be numeric only"})

        if database_id and not validate_numeric(database_id, "database_id"):
            return JSONResponse(status_code=400, content={"error": "database_id must be numeric only"})

        # Validate date parameters
        if not validate_date(start_date, "start_date"):
            return JSONResponse(status_code=400, content={"error": "start_date must be in YYYY-MM-DD format"})

        if not validate_date(end_date, "end_date"):
            return JSONResponse(status_code=400, content={"error": "end_date must be in YYYY-MM-DD format"})

        if df is None:
            return JSONResponse(status_code=500, content={"error": "CSV file could not be loaded."})
        filtered = df.copy()

        if subscription_id:
            filtered = filtered[filtered["Cluster id"].astype(str) == subscription_id]
        if database_id:
            # Filter by database ID, handling N/A values and float conversion
            # Convert database_id to float for comparison since CSV stores as float
            try:
                database_id_float = float(database_id)
                filtered = filtered[filtered["Database id"] == database_id_float]
            except ValueError:
                # If conversion fails, treat as string comparison
                filtered = filtered[filtered["Database id"].astype(str) == database_id]
        if plan_type:
            filtered = filtered[filtered["Plan Type"].str.lower() == plan_type.lower()]
        if start_date:
            filtered = filtered[filtered["Start date"] >= start_date]
        if end_date:
            filtered = filtered[filtered["End date"] <= end_date]
        if region:
            filtered = filtered[filtered["Region"] == region]
        if tag1:
            # Filter by tag1 value in key1:value column
            if "key1:value" in filtered.columns:
                filtered = filtered[filtered["key1:value"].astype(str).str.contains(tag1, na=False)]
        if tag2:
            # Filter by tag2 value in key2:value column
            if "key2:value" in filtered.columns:
                filtered = filtered[filtered["key2:value"].astype(str).str.contains(tag2, na=False)]

        if filtered.empty:
            return UsageReportResponse(data=[], total_rows=0)

        # Check if result count exceeds max_rows limit
        try:
            # Group by unique combinations to get distinct reports count
            unique_groups = filtered.groupby(
                ["Cluster id", "Cluster name", "Plan Type", "Region", "Start date", "End date"]
            ).first().reset_index()

            total_available = len(unique_groups)

            # If total available exceeds internal limit, return error
            if total_available > MAX_ROWS_LIMIT:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "RowLimitExceeded",
                        "message": f"The number of rows matching your request exceeds the allowed maximum of {MAX_ROWS_LIMIT}. Please adjust your filters."
                    }
                )

            # Sort by start date (newest to oldest) if within limit
            filtered_with_datetime = filtered.copy()
            filtered_with_datetime['_temp_start_date'] = pd.to_datetime(filtered_with_datetime['Start date'], errors='coerce')
            filtered_with_datetime = filtered_with_datetime.sort_values('_temp_start_date', ascending=False)

            # Sort the original data by the datetime order
            sort_order = filtered_with_datetime.index
            filtered = filtered.reindex(sort_order)

        except Exception as e:
            # If date parsing fails, continue without sorting
            pass

        # Detect tag columns (key:value)
        tag_columns = [col for col in filtered.columns if ":" in col]

        grouped = filtered.groupby(
            ["Cluster id", "Cluster name", "Plan Type", "Region", "Start date", "End date"]
        )

        results = []
        for key, group_df in grouped:
            charges = []
            for _, row in group_df.iterrows():
                # Collect tags if present
                tags = {k: str(row[k]) for k in tag_columns if pd.notnull(row[k])}
                charge_item_kwargs = dict(
                    charge_type=row.get("Charge Type"),
                    billing_unit_type=row.get("Billing Unit Type"),
                    quantity=row.get("Billing Unit quantity"),
                    price_per_hour=row.get("Billing Unit price/hr"),
                    hours=row.get("Hours"),
                    subtotal=row.get("Subtotal"),
                    discount=row.get("Discount"),
                    total_cost=row.get("Total Cost $")
                )
                if tags:
                    charge_item_kwargs["tags"] = tags
                charges.append(ChargeItem(**charge_item_kwargs))
            results.append(UsageReport(
                subscription_id=str(key[0]),
                cluster_name=key[1],
                plan_type=key[2],
                region=key[3],
                start_date=str(key[4]),
                end_date=str(key[5]),
                charges=charges
            ))

        # Clean NaN/inf values and return structured response
        cleaned_results = clean_nans([r.dict(exclude_none=True) for r in results])
        return UsageReportResponse(
            data=cleaned_results,
            total_rows=len(cleaned_results)
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
