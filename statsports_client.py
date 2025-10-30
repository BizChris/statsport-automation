# statsports_client.py
"""
Minimal Python client for STATSports Pro Series 3rd Party API.

- Supports either header-based auth (X-API-KEY / X-API-SECRET) **or** body-based auth (thirdPartyApiId in payload),
  and always sends an `api-version` header (default "7").
- Confirm your actual auth requirements in the Swagger UI here:
  https://statsportsproseries.com/thirdpartyapi/index.html?urls.primaryName=V7
- One documented path (v5 swagger) is `POST /api/thirdPartyData/getPlayerDetails` which expects an `api-version` header
  and a JSON body derived from a `ThirdPartyDto` schema containing `thirdPartyApiId` (UUID) and optional `sessionDate`.
  See the v5 snippet for reference.

Environment variables (set via shell or a .env file you load with python-dotenv):
    STATSPORTS_API_KEY        -> your 3rd party API key (UUID or token)
    STATSPORTS_API_SECRET     -> your API secret (if your tenant uses header-based auth)
    STATSPORTS_API_VERSION    -> "7" (or "5")  (defaults to 7)
    STATSPORTS_BASE_URL       -> defaults to "https://statsportsproseries.com/thirdpartyapi/api"
    STATSPORTS_AUTH_MODE      -> "headers" or "body" (defaults to "body")
    STATSPORTS_TIMEOUT_SECS   -> request timeout, defaults to 60

Usage example:
    from statsports_client import StatsportsClient
    client = StatsportsClient()
    # Example: fetch player details (payload depends on your tenant's set-up)
    payload = {"thirdPartyApiId": client.api_key}
    data = client.post("/ThirdPartyData/GetPlayerDetails", json=payload)
    client.to_csv(data, "player_details.csv")

DISCLAIMER:
    This is a pragmatic starter. Your tenant’s API might require slightly different headers/payloads.
    Check your Swagger UI and adjust AUTH_MODE and payload fields accordingly.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional, Union, List

import requests
import pandas as pd


class StatsportsClient:

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry: int = 2,
        backoff: float = 1.5,
    ) -> Any:
        """
        GET to an endpoint path under the base_url, returning JSON if possible.
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        hdrs = self._build_headers(headers)
        attempt = 0
        while True:
            attempt += 1
            try:
                resp = self._session.get(url, params=params, headers=hdrs, timeout=self.timeout)
                if 200 <= resp.status_code < 300:
                    try:
                        return resp.json()
                    except ValueError:
                        return resp.text
                if resp.status_code in (429, 500, 502, 503, 504) and attempt <= retry:
                    time.sleep(backoff ** attempt)
                    continue
                detail = None
                try:
                    detail = resp.json()
                except Exception:
                    detail = resp.text
                raise RuntimeError(f"HTTP {resp.status_code} for {url}: {detail}")
            except (requests.Timeout, requests.ConnectionError) as e:
                if attempt <= retry:
                    time.sleep(backoff ** attempt)
                    continue
                raise
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_version: Optional[str] = None,
        base_url: Optional[str] = None,
        auth_mode: Optional[str] = None,
        timeout: Optional[Union[int, float]] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("STATSPORTS_API_KEY", "").strip()
        self.api_secret = api_secret or os.getenv("STATSPORTS_API_SECRET", "").strip()
        self.api_version = (api_version or os.getenv("STATSPORTS_API_VERSION") or "7").strip()
        self.base_url = (base_url or os.getenv("STATSPORTS_BASE_URL") or "https://statsportsproseries.com/thirdpartyapi/api").rstrip("/")
        self.auth_mode = (auth_mode or os.getenv("STATSPORTS_AUTH_MODE") or "body").strip().lower()
        self.timeout = float(os.getenv("STATSPORTS_TIMEOUT_SECS", timeout or 60))

        if not self.api_key:
            raise ValueError("STATSPORTS_API_KEY is required. Set it in your environment or .env file.")

        if self.auth_mode not in {"body", "headers"}:
            raise ValueError('STATSPORTS_AUTH_MODE must be "body" or "headers".')

        # Simple session with retry-ish behavior
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})

    def _build_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "api-version": self.api_version,   # required by v5; assumed for v7 too
            "Content-Type": "application/json",
        }
        if self.auth_mode == "headers":
            # Common pattern; adjust header names if your swagger says otherwise.
            headers.update({
                "X-API-KEY": self.api_key,
            })
            if self.api_secret:
                headers["X-API-SECRET"] = self.api_secret

        if extra:
            headers.update(extra)
        return headers

    def _inject_auth_body(self, payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        payload = dict(payload or {})
        if self.auth_mode == "body":
            # v5 swagger hints at `thirdPartyApiId` (UUID) via ThirdPartyDto.
            # Many tenants map the "key" to this field.
            payload.setdefault("thirdPartyApiId", self.api_key)
        return payload

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry: int = 2,
        backoff: float = 1.5,
    ) -> Any:
        """
        POST to an endpoint path under the base_url, returning JSON if possible.

        :param path: e.g. "/ThirdPartyData/GetPlayerDetails" or "/thirdPartyData/getPlayerDetails"
        :param json: request payload; if auth_mode == "body", we add thirdPartyApiId if missing
        :param params: optional query params
        :param headers: optional extra headers
        :param retry: number of retries on transient 5xx and timeouts
        :param backoff: exponential backoff multiplier
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        payload = self._inject_auth_body(json)
        hdrs = self._build_headers(headers)

        attempt = 0
        while True:
            attempt += 1
            try:
                resp = self._session.post(url, json=payload, params=params, headers=hdrs, timeout=self.timeout)
                if 200 <= resp.status_code < 300:
                    try:
                        return resp.json()
                    except ValueError:
                        return resp.text
                # Retry on 429/5xx
                if resp.status_code in (429, 500, 502, 503, 504) and attempt <= retry:
                    time.sleep(backoff ** attempt)
                    continue
                # Surface useful error details
                detail = None
                try:
                    detail = resp.json()
                except Exception:
                    detail = resp.text
                raise RuntimeError(f"HTTP {resp.status_code} for {url}: {detail}")
            except (requests.Timeout, requests.ConnectionError) as e:
                if attempt <= retry:
                    time.sleep(backoff ** attempt)
                    continue
                raise

    @staticmethod
    def to_csv(data: Any, out_path: str) -> None:
        """
        Save JSON-like data to CSV, flattening nested structures where possible.
        """
        # If it's dict with a common "data" field, unwrap it
        if isinstance(data, dict) and "data" in data and isinstance(data["data"], (list, dict)):
            data = data["data"]

        # Convert to a list of records
        if isinstance(data, dict):
            records = [data]
        elif isinstance(data, list):
            records = data
        else:
            # If text, just write it raw
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(str(data))
            return

        # Flatten using pandas.json_normalize for better CSV columns
        df = pd.json_normalize(records, sep="_")
        df.to_csv(out_path, index=False)
        print(f"Saved {len(df)} rows -> {out_path}")
