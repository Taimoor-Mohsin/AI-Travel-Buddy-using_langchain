from src.agents.destination_parser import DestinationParserAgent
from src.agents.flight_hotel_scraper import FlightHotelScraperAgent


def test_destination_parser():
    agent = DestinationParserAgent()
    user_input = (
        "I'd like to visit Tokyo from September 12th to September 17th. "
        "My budget is around $2000 and I'm interested in anime and traditional food."
    )
    output = agent.run({"user_input": user_input})
    print("Agent output:", output)


def test_flight_hotel_sraper():
    agent = FlightHotelScraperAgent()
    # Use output from the parser agent as input here
    trip_request = {
        "destination": "Tokyo",
        "start_date": "September 12th",
        "end_date": "September 17th",
        "budget": 2000.0, # Note: Add a currency option and automatic conversion as well
        "preferences": ["anime", "traditional food"],
    }
    input_data = {"trip_request": trip_request}
    output = agent.run(input_data)
    print("Flight/Hotel Agent output:", output)


if __name__ == "__main__":
    test_destination_parser()
    test_flight_hotel_sraper()
