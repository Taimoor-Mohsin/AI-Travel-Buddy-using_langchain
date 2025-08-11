import sys
import json
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.integrations.travel_scraper.reference import (
    city_to_codes,
    search_airports_and_cities,
)


def pretty(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def main():
    print("=== Smoke test: Airport/City lookup ===")
    # 1) Free-text city name -> CITY + top AIRPORT
    city = "London"
    codes = city_to_codes(city)
    print(f"\ncity_to_codes('{city}') returned:")
    pretty(codes)

    # 2) IATA already -> should echo back
    print("\ncity_to_codes('LON') returned: ")
    pretty(city_to_codes("LON"))

    # 3) Raw listing (to eyeball multiple options)
    print("\nTop matches for keyword='New York' :")
    results = search_airports_and_cities("New York", limit=5)
    # Show only a few useful fields
    slim = [
        {
            "name": r.get("name"),
            "subType": r.get("subType"),
            "iataCode": r.get("iataCode"),
            "address": r.get("address", {}),
        }
        for r in results
    ]
    pretty(slim)


if __name__ == "__main__":
    try:
        main()
        print("\n✅ Reference lookup OK (OAuth also OK if you saw results above).")
    except Exception as e:
        print("\n❌ Test failed:")
        print(e)
        sys.exit(1)
