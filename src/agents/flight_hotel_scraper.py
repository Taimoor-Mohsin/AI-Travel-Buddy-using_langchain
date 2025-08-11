# src/agents/flight_hotel_scraper.py
from .base_agent import BaseAgent
from src.utils.logger import pretty_print

# Amadeus TEST env integrations you built & tested
from src.integrations.travel_scraper.reference import city_to_codes
from src.integrations.travel_scraper.flights import FlightQuery, search_flights
from src.integrations.travel_scraper.parsing import (
    summarize_offers_airports_and_carriers,
)

from src.integrations.travel_scraper.hotels import HotelQuery, search_hotels
from src.integrations.travel_scraper.parsing_hotels import summarize_hotels_offers


class FlightHotelScraperAgent(BaseAgent):
    """
    Pulls flight + hotel data from your Amadeus TEST integrations.

    - Flights: origin/dest codes -> Flight Offers Search -> tidy summaries (airports + carriers)
    - Hotels: Hotel List -> v3 Hotel Offers -> tidy summaries
    - Budget: allocate ~15% of total trip budget to hotels, filter out pricier ones
    """

    def __call__(self, state):
        return self.run(state)

    def run(self, input_data):
        # ---- 0) Validate incoming request (structured by the new UI) ----
        tr = input_data.trip_request or {}
        origin = (tr.get("origin") or "").strip() or (input_data.home_iata or "")
        destination = (tr.get("destination") or "").strip()
        start_date = tr.get("start_date")
        end_date = tr.get("end_date")
        currency = (input_data.currency or "USD").strip().upper()

        if not destination or not start_date or not end_date:
            return {
                "flight_options": [],
                "hotel_options": [],
                "error": "Missing destination and/or dates.",
            }

        # ---- 1) Resolve IATA city/airport codes ----
        # We accept either a city name ("Rome") or a code ("ROM"/"FCO")
        try:
            o_codes = city_to_codes(
                origin or "LHE"
            )  # fallback origin if user left blank
            d_codes = city_to_codes(destination)
        except Exception as e:
            return {
                "flight_options": [],
                "hotel_options": [],
                "error": f"IATA resolution failed: {e}",
            }

        origin_iata = o_codes["city"] or o_codes["airport"]
        dest_iata = d_codes["city"] or d_codes["airport"]

        # ---- 2) Flights (TEST env) ----
        try:
            fq = FlightQuery(
                origin_iata=origin_iata,
                dest_iata=dest_iata,
                depart_date=start_date,
                return_date=end_date,
                adults=1,
                currency=currency,
                max_results=20,
                travel_class="ECONOMY",
            )
            raw_offers = search_flights(fq)
            flight_summaries = summarize_offers_airports_and_carriers(raw_offers)
        except Exception as e:
            # Keep the app flowing; show friendly fallback
            flight_summaries = []
            print("Flight search failed:", e)

        # ---- 3) Hotels (Hotel List -> v3 Offers) ----
        try:
            hq = HotelQuery(
                city_code=d_codes["city"],  # e.g., "ROM"
                check_in=start_date,
                check_out=end_date,
                adults=1,
                currency=currency,
                max_hotels=40,  # ask more IDs; TEST data is sparse
            )
            v3_offers, hotel_list = search_hotels(hq)
            hotel_summaries = summarize_hotels_offers(v3_offers, hotel_list)
        except Exception as e:
            hotel_summaries = []
            print("Hotel search failed:", e)

        # ---- 4) Apply hotel budget filter (15% of total budget) ----
        budget_total = tr.get("budget")
        if isinstance(budget_total, (int, float)) and budget_total > 0:
            hotel_budget = float(budget_total) * 0.15
            hotel_summaries = [
                h
                for h in hotel_summaries
                if h.get("cheapest")
                and h["cheapest"].get("total")
                and float(h["cheapest"]["total"]) <= hotel_budget
            ]

        pretty_print("Flights (summaries)", flight_summaries[:5])
        pretty_print("Hotels (summaries)", hotel_summaries[:5])

        return {
            "flight_options": flight_summaries,
            "hotel_options": hotel_summaries,
        }
