from .base_agent import BaseAgent
from src.utils.logger import pretty_print
from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TravelBuddy/1.0)"}

# --- Helpers ---------------------------------------------------------------


def _clean_text(s):
    return re.sub(r"\s+", " ", s or "").strip()


def _first_ok(urls):
    """Return the first URL that returns 200 OK, else None."""
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                return url, r.text
        except Exception:
            pass
    return None, None


# --- Wikipedia: Airlines for the destination's likely airport --------------


def scrape_airlines_for_city(destination: str, start_date: str):
    """
    Try a few common Wikipedia page patterns for city airports and extract
    the 'Airlines and destinations' table. Returns a list of dicts with:
      { airline, price (placeholder), departure, arrival }
    """
    city = destination.strip()
    candidates = [
        f"https://en.wikipedia.org/wiki/{city.replace(' ', '_')}_International_Airport",
        f"https://en.wikipedia.org/wiki/{city.replace(' ', '_')}_airport",
        f"https://en.wikipedia.org/wiki/{city.replace(' ', '_')}_Airport",
        f"https://en.wikipedia.org/wiki/{city.replace(' ', '_')}",
    ]

    url, html = _first_ok(candidates)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    # Look for a section/table with airlines; this varies by page.
    # Strategy: find any table with 'Airlines' or 'Destinations' in header rows.
    tables = soup.find_all(
        "table", class_=lambda x: x and ("wikitable" in x or "sortable" in x)
    )
    airlines = set()
    results = []

    for table in tables:
        headers = [_clean_text(th.get_text()) for th in table.find_all("th")]
        header_str = " | ".join(headers).lower()

        if ("airline" in header_str and "destination" in header_str) or (
            "airlines" in header_str
        ):
            # Parse rows
            for row in table.find_all("tr"):
                cells = row.find_all(["td", "th"])
                texts = [_clean_text(c.get_text(" ")) for c in cells]
                if len(texts) < 2:
                    continue

                # Heuristics: try to find the airline name in the first 1-2 columns
                airline = None
                for idx in range(min(2, len(texts))):
                    t = texts[idx]
                    # If a cell contains many commas, it's not just an airline name, skip
                    if len(t) > 1 and len(t) < 80:
                        airline = t
                        break

                if airline:
                    # Avoid dumping big paragraphs like notes
                    airline = airline.split("[")[0].strip()  # drop footnote markers
                    if airline and airline.lower() not in ("airline", "airlines"):
                        airlines.add(airline)

    # Build results with placeholders for price (we'll keep float for schema continuity)
    for airline in list(airlines)[:6]:  # limit to a few for UI
        results.append(
            {
                "airline": airline,
                "price": 0.0,  # placeholder; real prices require APIs or vendor scraping
                "departure": f"Home Airport - {start_date}",
                "arrival": f"{destination} - {start_date}",
            }
        )

    return results


# --- Wikivoyage: Sleep section for hotels ----------------------------------


def scrape_hotels_for_city(destination: str):
    """
    Scrape the 'Sleep' section from Wikivoyage for the destination.
    Returns a list of dicts:
      { provider, price, details }
    """
    city = destination.strip()
    candidates = [
        f"https://en.wikivoyage.org/wiki/{city.replace(' ', '_')}",
        f"https://en.wikivoyage.org/wiki/{city.replace(' ', '_')},_{city.replace(' ', '_')}",  # fallback pattern
    ]
    url, html = _first_ok(candidates)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    # Find the "Sleep" section heading
    # Headings on Wikivoyage are usually h2/h3 with a span id or text "Sleep"
    sleep_header = None
    for tag in soup.find_all(["h2", "h3"]):
        txt = _clean_text(tag.get_text()).lower()
        if "sleep" in txt:
            sleep_header = tag
            break

    if not sleep_header:
        return []

    # Collect list items until the next heading of the same or higher level
    hotels = []
    for sibling in sleep_header.find_all_next():
        if sibling.name in ("h2", "h3"):  # reached next section
            break
        if sibling.name in ("ul", "ol"):
            for li in sibling.find_all("li", recursive=False):
                # Heuristic: many entries have a bolded name + description
                name_tag = li.find(["b", "strong", "a"])
                name = _clean_text(name_tag.get_text()) if name_tag else None

                desc = _clean_text(li.get_text(" "))
                # Remove the name from the description if duplicated
                if name:
                    if desc.lower().startswith(name.lower()):
                        desc = _clean_text(desc[len(name) :])

                # Try to infer a rough price range symbol if present ($, $$, $$$)
                price_hint = None
                m = re.search(r"(\${1,4})", desc)
                if m:
                    price_hint = m.group(1)

                if name:
                    hotels.append(
                        {
                            "provider": name,
                            "price": (
                                0.0 if not price_hint else float(len(price_hint) * 50)
                            ),  # rough fake mapping
                            "details": desc[:300],  # trim long blurbs
                        }
                    )

        # Cap results for UI sanity
        if len(hotels) >= 6:
            break

    return hotels


# --- Public function used by the agent -------------------------------------


def fetch_flights_and_hotels(destination: str, start_date: str, end_date: str):
    """
    Combine airline scrape (Wikipedia airport page) + hotel scrape (Wikivoyage Sleep).
    Everything is open/free and relatively bot-friendly.
    """
    # You can attach date parsing or seasonal logic here later if needed
    flight_options = scrape_airlines_for_city(destination, start_date)
    hotel_options = scrape_hotels_for_city(destination)

    # If both scrapes fail, provide a gentle fallback (so the app doesn't feel broken)
    if not flight_options:
        flight_options = [
            {
                "airline": "Data not available",
                "price": 0.0,
                "departure": f"Home Airport - {start_date}",
                "arrival": f"{destination} - {start_date}",
            }
        ]

    if not hotel_options:
        hotel_options = [
            {
                "provider": f"{destination} — No 'Sleep' listings found",
                "price": 0.0,
                "details": "Try a different city spelling, or pick a major city.",
            }
        ]

    return {"flight_options": flight_options, "hotel_options": hotel_options}


# --- Agent -----------------------------------------------------------------


class FlightHotelScraperAgent(BaseAgent):
    """
    Agent that retrieves flight and hotel information based on trip request details.
    Output:
      {
        "flight_options": [ { airline, price, departure, arrival }, ... ],
        "hotel_options":  [ { provider, price, details }, ... ]
      }
    """

    def run(self, input_data):
        if not input_data.trip_request:
            return {
                "flight_options": [],
                "hotel_options": [],
                "error": "No trip details provided.",
            }

        trip = input_data.trip_request
        destination = trip.get("destination", "").strip()
        start_date = trip.get("start_date", "")
        end_date = trip.get("end_date", "")

        data = fetch_flights_and_hotels(destination, start_date, end_date)

        # Pretty print for debugging/demo
        pretty_print("flight_options", data["flight_options"])
        pretty_print("hotel_options", data["hotel_options"])

        return data

    def __call__(self, state):
        return self.run(state)
