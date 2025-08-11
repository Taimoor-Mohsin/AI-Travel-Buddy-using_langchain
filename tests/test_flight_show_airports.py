"""
tests/test_flights_show_airports.py
-----------------------------------
Fetches flight offers and prints, for each offer:
- price, currency
- OUTBOUND: from_airport -> to_airport with times and stops
- INBOUND:  same (if present)

This mirrors what you'd show the user in your app.
"""

import sys
import json
from pathlib import Path

# Ensure project imports work when running this file directly
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.integrations.travel_scraper.reference import city_to_codes
from src.integrations.travel_scraper.flights import FlightQuery, search_flights
from src.integrations.travel_scraper.parsing import (
    summarize_offers_airports_and_carriers,
)


def pretty(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def main():
    print("=== Show per-offer origin & destination airports ===")

    # Use CITY codes so we can see variation in actual airports used
    origin_city = "LHE"
    dest_city = "Rome"

    origin_codes = city_to_codes(
        origin_city
    )  # e.g., {'city':'LHE','airport':'LHE'} for Lahore
    dest_codes = city_to_codes(dest_city)  # e.g., {'city':'ROM','airport':'FCO'}

    q = FlightQuery(
        origin_iata=origin_codes["city"],  # 'LHE' (city==airport here)
        dest_iata=dest_codes["city"],  # 'ROM' so flights may land at FCO or CIA
        depart_date="2025-09-12",
        return_date="2025-09-17",
        adults=1,
        currency="USD",
        max_results=20,
        travel_class="ECONOMY",
    )

    offers = search_flights(q)
    print(f"Total offers: {len(offers)}")

    summaries = summarize_offers_airports_and_carriers(offers)

    # Print the first 5 neatly
    pretty(summaries[:5])

    print("\nTip: In your UI, list each offer with:")
    print(
        " - OUTBOUND: {from_airport} → {to_airport} ({depart_time} → {arrive_time}, stops={stops})"
    )
    print(" - INBOUND:  same (if round-trip)")


if __name__ == "__main__":
    try:
        main()
        print("\n✅ Show-airports test completed.")
    except Exception as e:
        print("\n❌ Test failed:")
        print(e)
        sys.exit(1)
