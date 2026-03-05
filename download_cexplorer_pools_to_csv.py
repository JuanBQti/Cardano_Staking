#!/usr/bin/env python3
"""
Download all staking pools from Cexplorer and save to CSV.

Usage:
  export CEXPLORER_API_KEY="your_api_key"
  python3 download_cexplorer_pools_to_csv.py

Optional:
  python3 download_cexplorer_pools_to_csv.py --output staking_pools.csv --limit 100
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from typing import Any, Dict, Iterable, List

import requests


BASE_URLS = [
    "https://api-mainnet-stage.cexplorer.io/v1/pool/list",
    "https://api-mainnet.cexplorer.io/v1/pool/list",
]


def flatten_dict(data: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    flat: Dict[str, Any] = {}
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            flat.update(flatten_dict(value, new_key, sep=sep))
        elif isinstance(value, list):
            # Keep list values as JSON-like strings for CSV compatibility.
            flat[new_key] = str(value)
        else:
            flat[new_key] = value
    return flat


def extract_rows(payload: Dict[str, Any]) -> tuple[List[Dict[str, Any]], int | None]:
    # Common Cexplorer shape:
    # { "code": 200, "data": { "data": [...], "count": 1234 }, ... }
    wrapper = payload.get("data", {})
    if isinstance(wrapper, dict):
        rows = wrapper.get("data", [])
        count = wrapper.get("count")
    else:
        rows = []
        count = None

    if not isinstance(rows, list):
        rows = []
    if not isinstance(count, int):
        count = None
    return rows, count


def _build_auth_headers(api_key: str) -> Dict[str, str]:
    return {
        "api-key": api_key,
        "x-api-key": api_key,
        "authorization": f"Bearer {api_key}",
        "accept": "application/json",
        "user-agent": "cexplorer-pool-export/1.0",
        "origin": "https://cexplorer.io",
        "referer": "https://cexplorer.io/",
    }


def _response_details(response: requests.Response) -> str:
    body = response.text.strip()
    if len(body) > 600:
        body = body[:600] + "...(truncated)"
    return f"HTTP {response.status_code}; body: {body or '<empty>'}"


def fetch_all_pools(api_key: str, limit: int = 100, sleep_s: float = 0.12) -> List[Dict[str, Any]]:
    headers = _build_auth_headers(api_key)
    offset = 0
    all_rows: List[Dict[str, Any]] = []
    expected_total: int | None = None
    last_error = ""
    session = requests.Session()
    # Avoid inheriting any local proxy variables that can break requests.
    session.trust_env = False

    while True:
        params_base = {
            "limit": limit,
            "offset": offset,
            "order": "live_stake",
            "sort": "desc",
        }
        response = None

        # Try known API host variants. Some accounts/environments only allow one.
        for base_url in BASE_URLS:
            # Some gateways expect API key strictly in headers, others accept query param.
            candidate_params = [
                dict(params_base),
                dict(params_base, **{"api-key": api_key}),
                dict(params_base, **{"apikey": api_key}),
            ]
            for params in candidate_params:
                response = session.get(base_url, headers=headers, params=params, timeout=45)
                if response.status_code in (200, 401):
                    break
                last_error = f"{base_url} -> {_response_details(response)}"
            if response is not None and response.status_code in (200, 401):
                break

        if response is None:
            raise RuntimeError("No response received from API.")
        if response.status_code == 401:
            raise RuntimeError("Unauthorized (401). Check your CEXPLORER_API_KEY.")
        if response.status_code == 403:
            detail = _response_details(response)
            raise RuntimeError(
                "Forbidden (403). Your key may not be activated for API access yet "
                f"or additional project setup is required. Details: {detail}"
            )
        if response.status_code != 200:
            detail = _response_details(response)
            if last_error:
                detail = f"{detail}; last fallback error: {last_error}"
            raise RuntimeError(f"Unexpected API response. {detail}")

        try:
            payload = response.json()
        except json.JSONDecodeError:
            raise RuntimeError(f"API did not return JSON. {_response_details(response)}")
        rows, count = extract_rows(payload)
        if expected_total is None:
            expected_total = count

        if not rows:
            break

        all_rows.extend(rows)
        offset += len(rows)

        if expected_total is not None and len(all_rows) >= expected_total:
            break

        if len(rows) < limit:
            break

        time.sleep(sleep_s)

    return all_rows


def rows_to_csv(rows: Iterable[Dict[str, Any]], output_path: str) -> int:
    flat_rows = [flatten_dict(row) for row in rows]
    if not flat_rows:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["message"])
            writer.writerow(["No pool rows returned by API"])
        return 0

    fieldnames = sorted({k for row in flat_rows for k in row.keys()})
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(flat_rows)
    return len(flat_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download all Cexplorer staking pools to CSV.")
    parser.add_argument("--output", default="staking_pools.csv", help="Output CSV path")
    parser.add_argument("--limit", type=int, default=100, help="Page size (recommended max 100)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit < 1 or args.limit > 100:
        print("Error: --limit must be between 1 and 100.", file=sys.stderr)
        return 2

    api_key = os.getenv("CEXPLORER_API_KEY", "").strip()
    if not api_key:
        print(
            "Error: missing API key. Set env var CEXPLORER_API_KEY first.",
            file=sys.stderr,
        )
        return 2

    try:
        rows = fetch_all_pools(api_key=api_key, limit=args.limit)
    except Exception as exc:  # pragma: no cover - runtime-safe reporting
        print(f"Failed to download pools: {exc}", file=sys.stderr)
        return 1

    count = rows_to_csv(rows, args.output)
    print(f"Wrote {count} pool rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
