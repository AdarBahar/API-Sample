from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
import pandas as pd
import numpy as np
from fastapi.responses import JSONResponse
import os
import math

app = FastAPI(title="Usage & Cost API", version="2.3")

CSV_FILE = "cost_report.csv"

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

@app.get("/api/v1/usage-report", response_model=List[UsageReport])
def get_usage_report(
    subscription_id: Optional[str] = Query(None, description="Filter by subscription/cluster ID."),
    plan_type: Optional[str] = Query(None, description="Filter by plan type."),
    start_date: Optional[str] = Query(None, description="Filter for usage starting on or after this date (format: YYYY-MM-DD)."),
    end_date: Optional[str] = Query(None, description="Filter for usage ending on or before this date (format: YYYY-MM-DD)."),
    region: Optional[str] = Query(None, description="Filter by region.")
):
    """Get usage and cost report.

    All query parameters are optional. You may use none, any, or all of them in combination to filter results.

    - `subscription_id`: Filter by subscription/cluster ID.
    - `plan_type`: Filter by plan type.
    - `start_date`: Filter for usage starting on or after this date (format: YYYY-MM-DD).
    - `end_date`: Filter for usage ending on or before this date (format: YYYY-MM-DD).
    - `region`: Filter by region.

    Date format for `start_date` and `end_date` must be `YYYY-MM-DD`.
    """
    try:
        if df is None:
            return JSONResponse(status_code=500, content={"error": "CSV file could not be loaded."})
        filtered = df.copy()

        if subscription_id:
            filtered = filtered[filtered["Cluster id"].astype(str) == subscription_id]
        if plan_type:
            filtered = filtered[filtered["Plan Type"].str.lower() == plan_type.lower()]
        if start_date:
            filtered = filtered[filtered["Start date"] >= start_date]
        if end_date:
            filtered = filtered[filtered["End date"] <= end_date]
        if region:
            filtered = filtered[filtered["Region"] == region]

        if filtered.empty:
            return []

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
                start_date=key[4],
                end_date=key[5],
                charges=charges
            ))

        # Clean NaN/inf values before returning
        return clean_nans([r.dict(exclude_none=True) for r in results])

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
