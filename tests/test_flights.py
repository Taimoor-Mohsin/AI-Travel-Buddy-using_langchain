"""
tests/test_flights.py
---------------------
Small smoke test for Flight Offers Search.

Notes:
- The Amadeus TEST environment has limited, cached data. If your chosen route/dates
  return 0 results, try different dates or a busier route (e.g., LHE->LON/ROM/DXB).
- This test only prints counts and a tiny preview so you can eyeball the shape.
"""

import sys
import json
from pathlib import Path

# Make project modules importable when running "python tests/test_flights.py"
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.integrations.travel_scraper.reference import city_to_codes
from src.integrations.travel_scraper.flights import FlightQuery, search_flights


def pretty(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def main():
    print("=== Smoke test: Flight Offers ===")

    # --- 1) Resolve destination codes (CITY + representative AIRPORT) ---
    # Input TYPE: str
    dest_city_name = "Rome"
    codes = city_to_codes(dest_city_name)  # Return Type is dict[str, str]
    print(f"Resolved codes for '{dest_city_name}':")
    pretty(codes)

    # --- 2) Build a typed flight query ---
    # Using "city" code for destination means any airport in the metro (ROM); use "airport" for a specific one (FCO).
    q = FlightQuery(
        origin_iata="LHE",
        dest_iata=codes["city"],
        depart_date="2025-09-12",
        return_date="2025-09-15",
        adults=1,
        currency="USD",
        max_results=10,
        max_price=None,
        non_stop=None,
        travel_class="ECONOMY",
    )

    # --- 3) Call the API ---
    offers = search_flights(q)  # RETURN TYPE: list[dict]
    print(f"\nOffers Found: {len(offers)}")
    # --- 4) Show a tiny preview (first offer's summarized fields) ---
    if offers:
        o = offers[0]
        # Defensive access with dict.get to avoid KeyError if a field is absent.
        summary = {
            "itineraries": len(o.get("itineraries", [])),
            "price_total": o.get("price", {}).get("grandTotal"),
            "currency": o.get("price", {}).get("currency"),
            "one_example_segment": (
                o.get("itineraries", [{}])[0]
                .get("segments", [{}])[0]
                .get("carrierCode", None)
            ),
        }
        print("\nPreview of first offer:")
        pretty(summary)
    else:
        print(
            "No offers returned. Try different dates/routes (TEST env can be sparse)."
        )


if __name__ == "__main__":
    try:
        main()
        print("\n✅ Flight search smoke test completed.")
    except Exception as e:
        print("\n❌ Test failed:")
        print(e)
        sys.exit(1)
