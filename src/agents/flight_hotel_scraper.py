from .base_agent import BaseAgent
from src.utils.logger import pretty_print
from src.schema.travel_models import TripRequest, FlightOption, AccommodationOption

# For real scraping(to be added later), we will import requests/bs4
# For now, for demo purposes and testing we will use mock data


class FlightHotelScraperAgent(BaseAgent):
    def __call__(self, state):
        return self.run(state)

    def run(self, input_data):
        # Getting trip details
        trip_info = input_data.trip_request
        if not trip_info:
            return {
                "flight_options": [],
                "hotel_options": [],
                "error": "No trip details provided",
            }

        # For demo and testing: Using TripRequest to make it flexible!
        trip = TripRequest(**trip_info)
        destination = trip.destination
        start_date = trip.start_date
        end_date = trip.end_date

        # Mock data for flights (real scraping will be added later)
        flight_options = [
            FlightOption(
                airline="Grow Airways",
                price=450.0,
                departure=f"Home Airport - {start_date}",
                arrival=f"{destination} - {start_date}",
            ),
            FlightOption(
                airline="LangChain Airlines",
                price=520.0,
                departure=f"Home Airport - {start_date}",
                arrival=f"{destination} - {start_date}",
            ),
        ]

        # Mock data for hotels
        hotel_options = [
            AccommodationOption(
                provider=f"{destination} Central Hotel",
                price=120.0,
                details="3-star, city center, breakfast included",
            ),
            AccommodationOption(
                provider=f"{destination} Capsule Inn",
                price=65.0,
                details="Budget capsule hotel",
            ),
        ]

        flight_data = [f.dict() for f in flight_options]
        hotel_data = [h.dict() for h in hotel_options]

        pretty_print("Flight Options:", flight_data)
        pretty_print("Hotel Options:", hotel_data)

        return {"flight_options": flight_data, "hotel_options": hotel_data}
