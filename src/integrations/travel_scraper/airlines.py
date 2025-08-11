"""
airlines.py
-----------
Map airline carrier codes (e.g., "QR") to readable names ("Qatar Airways")
using Amadeus Airline Code Lookup.
"""

from __future__ import annotations
from typing import Dict, List
from .amadeus_client import AmadeusClient

# Simple in-memory cache so repeated lookups don't hit your quota.
# KEY: code string ("QR"), VALUE: airline name ("Qatar Airways")
_CODE_NAME_CACHE: Dict[str, str] = {}


def map_airline_codes_to_names(codes: List[str]) -> Dict[str, str]:
    """
    Accepts a list of airline codes and returns {code: name}.

    - Deduplicates input codes
    - Uses a simple cache to avoid repeated network calls
    - Falls back to "Unknown Airline" for anything not returned by the API
    """
    # 1) Normalize & dedupe inputs (skip falsy: None/"")
    uniq = [c for c in dict.fromkeys(codes) if c]
    if not uniq:
        return {}

    # 2) Check cache first
    to_fetch = [c for c in uniq if c not in _CODE_NAME_CACHE]
    if to_fetch:
        cli = AmadeusClient()
        # Official endpoint: /v1/reference-data/airlines
        resp = cli.get(
            "/v1/reference-data/airlines", {"airlineCodes": ",".join(to_fetch)}
        )
        for item in resp.get("data", []):
            code = item.get("iataCode") or item.get("icaoCode")
            # prefer a stable, human-friendly name:
            name = (
                item.get("businessName") or item.get("commonName") or item.get("name")
            )
            if code and name:
                _CODE_NAME_CACHE[code] = str(name).title()

    # 3) Build final mapping, fill missing with placeholder
    return {c: _CODE_NAME_CACHE.get(c, "Unknown Airline") for c in uniq}
