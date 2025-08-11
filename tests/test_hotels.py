"""
tests/test_hotels.py
--------------------
End-to-end TEST of the v3 hotel flow:
  City code -> Hotel List -> hotelIds -> Hotel Offers v3 -> summarized output
"""

import sys, json
from pathlib import Path

# Allow running from repo root
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.integrations.travel_scraper.reference import city_to_codes
from src.integrations.travel_scraper.hotels import HotelQuery, search_hotels
from src.integrations.travel_scraper.parsing_hotels import summarize_hotels_offers


def pretty(x):
    print(json.dumps(x, indent=2, ensure_ascii=False))


def main():
    total_budget = 2000  # USD entered by user
    hotel_budget = total_budget * 0.15  # 15% allocation

    codes = city_to_codes("Rome")

    q = HotelQuery(
        city_code=codes["city"],
        check_in="2025-09-12",
        check_out="2025-09-17",
        adults=1,
        currency="USD",
        max_hotels=50,
    )

    v3_offers, hotel_list = search_hotels(q)

    # Summarize and filter by budget
    summaries = summarize_hotels_offers(v3_offers, hotel_list)
    summaries = [
        h
        for h in summaries
        if h["cheapest"] and float(h["cheapest"]["total"]) <= hotel_budget
    ]

    print(f"Hotels within budget (${hotel_budget:.2f}): {len(summaries)}")
    pretty(summaries[:5])


if __name__ == "__main__":
    try:
        main()
        print("\n✅ Hotels smoke test completed.")
    except Exception as e:
        print("\n❌ Test failed:")
        print(e)
        sys.exit(1)
