#!/usr/bin/env python3
"""
Test script for MWID External API Endpoints (Sales & Investors).

Tests all 4 endpoints:
  - GET /api/v1/external/manual-sales
  - GET /api/v1/external/manual-sales/:id
  - GET /api/v1/external/manual-investors
  - GET /api/v1/external/manual-investors/:id

Usage:
  export MWID_EXTERNAL_API_KEY="mw_..."
  python test_api.py
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://mwid.up.railway.app/api/v1/external"
API_KEY = os.environ.get("MWID_EXTERNAL_API_KEY", "")

if not API_KEY:
    print("❌ ERROR: Set MWID_EXTERNAL_API_KEY environment variable first.")
    print('   export MWID_EXTERNAL_API_KEY="mw_..."')
    sys.exit(1)

HEADERS = {"X-API-Key": API_KEY}

# ── Helpers ──────────────────────────────────────────────────────────────────

def sep(title: str):
    print(f"\n{'═' * 60}")
    print(f"  {title}")
    print(f"{'═' * 60}")


def pretty(data, max_items: int = 2):
    """Print JSON data, truncating arrays to max_items for readability."""
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
        truncated = {
            **data,
            "data": data["data"][:max_items],
            "_shown": f"{min(max_items, len(data['data']))} of {len(data['data'])} items",
        }
        print(json.dumps(truncated, indent=2, default=str))
    else:
        print(json.dumps(data, indent=2, default=str))


def test_get(label: str, url: str, params: dict | None = None) -> dict | None:
    """Make a GET request, print result, return JSON or None on failure."""
    print(f"\n🔹 {label}")
    print(f"   GET {url}")
    if params:
        print(f"   Params: {params}")

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        print(f"   Status: {resp.status_code}")
        if resp.ok:
            data = resp.json()
            pretty(data)
            return data
        else:
            print(f"   ❌ Response: {resp.text[:300]}")
            return None
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None

# ── Tests ────────────────────────────────────────────────────────────────────

def test_sales():
    sep("MANUAL SALES")

    # 1. List sales (default pagination)
    result = test_get(
        "List sales (default pagination)",
        f"{BASE_URL}/manual-sales",
    )

    # 2. List sales with custom pagination
    test_get(
        "List sales (page=1, pageSize=5)",
        f"{BASE_URL}/manual-sales",
        params={"page": 1, "pageSize": 5},
    )

    # 3. Get single sale by ID (using first item from list)
    if result and result.get("data"):
        first = result["data"][0]
        sale_id = first.get("id") or first.get("_id")
        if sale_id:
            test_get(
                f"Get sale by ID ({sale_id})",
                f"{BASE_URL}/manual-sales/{sale_id}",
            )
        else:
            print("\n⚠️  Could not determine ID field from first sale item.")
            print(f"   Keys: {list(first.keys())}")
    else:
        print("\n⚠️  Skipping single-sale test — no data returned.")

    # 4. Test filter params (won't error even if no matches)
    test_get(
        "List sales with filter (adjustmentType=bonus)",
        f"{BASE_URL}/manual-sales",
        params={"adjustmentType": "bonus", "pageSize": 3},
    )


def test_investors():
    sep("MANUAL INVESTORS")

    # 1. List investors (default pagination)
    result = test_get(
        "List investors (default pagination)",
        f"{BASE_URL}/manual-investors",
    )

    # 2. List investors with custom pagination
    test_get(
        "List investors (page=1, pageSize=5)",
        f"{BASE_URL}/manual-investors",
        params={"page": 1, "pageSize": 5},
    )

    # 3. Get single investor by ID (using first item from list)
    if result and result.get("data"):
        first = result["data"][0]
        investor_id = first.get("id") or first.get("_id")
        if investor_id:
            test_get(
                f"Get investor by ID ({investor_id})",
                f"{BASE_URL}/manual-investors/{investor_id}",
            )
        else:
            print("\n⚠️  Could not determine ID field from first investor item.")
            print(f"   Keys: {list(first.keys())}")
    else:
        print("\n⚠️  Skipping single-investor test — no data returned.")

    # 4. Test filter params
    test_get(
        "List investors with filter (country=Romania)",
        f"{BASE_URL}/manual-investors",
        params={"country": "Romania", "pageSize": 3},
    )


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 MWID External API Test")
    print(f"   Base URL: {BASE_URL}")
    print(f"   API Key:  {API_KEY[:8]}...{API_KEY[-4:]}")

    test_sales()
    test_investors()

    sep("DONE")
    print("✅ All tests completed.\n")
