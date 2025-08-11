"""
tests/test_flights_demo_testenv.py
----------------------------------
Goal (TEST env friendly):
- Fetch flight offers
- Summarize each offer with airports, times, stops, carriers (+ names)
- DEDUPLICATE near-identical offers so the list is clean
- (Optional) Add a clearly-marked "demo jitter" to prices to preview UI behavior
  without having Production keys. This never touches real data; it's for display.

USAGE:
    # Activate your venv first
    # source venv/Scripts/activate  (or .venv/Scripts/activate)

    # Regular run (no jitter):
    python tests/test_flights_demo_testenv.py

    # With jitter for demo (adds +/- a few % to printed price ONLY):
    DEMO_JITTER=1 python tests/test_flights_demo_testenv.py
"""

import os
import sys
import json
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP

# Make project modules importable when running this file directly
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.integrations.travel_scraper.reference import city_to_codes
from src.integrations.travel_scraper.flights import FlightQuery, search_flights
from src.integrations.travel_scraper.parsing import (
    summarize_offers_airports_and_carriers,
)


def pretty(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def _price_to_decimal(s: str | None):
    """
    Convert a price string like "954.20" to Decimal for safe math.
    Returns Decimal or None.
    """
    try:
        return Decimal(s)
    except Exception:
        return None


def _signature_for_dedup(summary: dict) -> tuple:
    """
    Build a tuple key that represents an offer "shape" so we can deduplicate.

    We use outbound/inbound airports & times + carrier list + price to detect near-duplicates.
    Adjust fields to make it stricter or looser depending on your needs.
    """
    out = summary.get("outbound") or {}
    inb = summary.get("inbound") or {}

    return (
        out.get("from_airport"),
        out.get("depart_time"),
        out.get("to_airport"),
        tuple(out.get("carriers", [])),
        inb.get("from_airport"),
        inb.get("depart_time"),
        inb.get("to_airport"),
        tuple(inb.get("carriers", [])),
        summary.get("price_total"),  # string price; okay for equality checks
        summary.get("currency"),
    )


def _maybe_jitter_price(summary: dict, enabled: bool) -> dict:
    """
    For TEST env demo ONLY:
    - If enabled, compute a small deterministic "jitter" (based on the offer id)
      and apply it to the DISPLAYED price so your UI doesn't look identical.
    - We never mutate the original offer or send jittered prices anywhere else.

    Returns a shallow copy with adjusted "price_total" string.
    """
    if not enabled:
        return summary

    price_str = summary.get("price_total")
    price = _price_to_decimal(price_str)
    if price is None:
        return summary

    # Deterministic jitter: hash the id to choose +/- 0%..4%
    oid = summary.get("id") or ""
    h = sum(ord(c) for c in str(oid)) % 5  # 0..4
    percent = Decimal(h) / Decimal(100)  # 0.00, 0.01, ... 0.04
    # alternate sign for a bit of spread
    sign = Decimal(-1) if (sum(ord(c) for c in str(oid)) % 2 == 0) else Decimal(1)
    jittered = (price + (price * percent * sign)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    clone = dict(summary)
    clone["price_total"] = str(jittered)
    clone["price_note"] = "TEST-ENV DEMO (price visually jittered)"
    return clone


def main():
    print("=== TEST-ENV Demo: dedup + per-offer airport/carrier ===")

    # Use city codes so multiple airports may appear in results
    origin = "LHE"  # Lahore (city=airport)
    dest_city = "Rome"
    dest_codes = city_to_codes(dest_city)  # {'city':'ROM','airport':'FCO'}

    q = FlightQuery(
        origin_iata=origin,
        dest_iata=dest_codes["city"],  # 'ROM' so FCO/CIA are possible arrivals
        depart_date="2025-09-12",
        return_date="2025-09-17",
        adults=1,
        currency="USD",
        max_results=50,  # ask for more; TEST env may still give limited variety
        travel_class="ECONOMY",
    )

    offers = search_flights(q)
    print(f"Raw offers (possibly repetitive in TEST): {len(offers)}")

    # Build readable summaries (airports, times, stops, carriers + names)
    summaries = summarize_offers_airports_and_carriers(offers)

    # Deduplicate near-identical offers for a cleaner list
    deduped = {}
    for s in summaries:
        key = _signature_for_dedup(s)
        deduped.setdefault(key, s)

    clean_list = list(deduped.values())
    print(f"Unique offers after dedup: {len(clean_list)}")

    # Optional: visually jitter price just for the demo (env var toggle)
    jitter_enabled = os.getenv("DEMO_JITTER") == "1"
    if jitter_enabled:
        clean_list = [_maybe_jitter_price(s, enabled=True) for s in clean_list]

    # Show first 8
    preview = clean_list[:8]
    pretty(preview)

    print("\nNotes:")
    print("- TEST env often returns repetitive data; dedup helps your UI.")
    print("- Set DEMO_JITTER=1 to visually vary prices for demos (display only).")
    print("- For real-time fares/availability, switch to Production keys later.")


if __name__ == "__main__":
    try:
        main()
        print("\n✅ TEST-ENV demo completed.")
    except Exception as e:
        print("\n❌ Test failed:")
        print(e)
        sys.exit(1)
