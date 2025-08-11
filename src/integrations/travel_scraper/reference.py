from typing import Dict, List
from src.integrations.travel_scraper.amadeus_client import AmadeusClient, AmadeusError


def search_airports_and_cities(keyword: str, limit: int = 5) -> List[dict]:
    cli = AmadeusClient()
    params = {"keyword": keyword, "subType": "CITY,AIRPORT", "page[limit]": limit}
    data = cli.get("/v1/reference-data/locations", params)
    return data.get("data", [])


def city_to_codes(city_or_iata: str) -> Dict[str, str]:
    s = city_or_iata.upper()
    if len(s) == 3:  # LHE, KHI,etc
        return {"city": s, "airport": s}

    items = search_airports_and_cities(city_or_iata, limit=5)
    if not items:
        raise AmadeusError(f"No IATA match for '{city_or_iata}'")

    city_code = None
    airport_code = None
    for it in items:
        if it.get("subType") == "CITY" and not city_code:
            city_code = it.get("iataCode")
        if it.get("subType") == "AIRPORT" and not airport_code:
            airport_code = it.get("iataCode")

    # Fallback to top result if one type missing
    code = items[0].get("iataCode")
    return {"city": city_code or code, "airport": airport_code or code}
