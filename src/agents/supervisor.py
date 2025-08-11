# src/agents/supervisor.py
from langgraph.graph import StateGraph
from src.agents.destination_parser import DestinationParserAgent
from src.agents.flight_hotel_scraper import FlightHotelScraperAgent
from src.agents.itinerary_agent import ItineraryAgent
from src.agents.packing_list_agent import PackingListAgent
from src.agents.reminder_agent import ReminderAgent
from src.schema.travel_models import TravelBuddyState
from typing import Optional, List, Dict, Any, Union


class TravelBuddySupervisor:
    def __init__(self):
        self.graph = StateGraph(state_schema=TravelBuddyState)
        self._build_graph()
        # StateGraph defines the workflow, to run it, it must be compiled into a runnable object first
        # First I was using run(), .invoke() needs to be used to execute
        self.runnable_graph = self.graph.compile()

    def _build_graph(self):
        # Add nodes (agents) to the workflow graph
        self.graph.add_node("destination_parser", DestinationParserAgent())
        self.graph.add_node("flight_hotel_scraper", FlightHotelScraperAgent())
        self.graph.add_node("itinerary_agent", ItineraryAgent())
        self.graph.add_node("packing_list_agent", PackingListAgent())
        self.graph.add_node("reminder_agent", ReminderAgent())

        # Define the data flow (edges)
        self.graph.add_edge("destination_parser", "flight_hotel_scraper")
        self.graph.add_edge("flight_hotel_scraper", "itinerary_agent")
        self.graph.add_edge("itinerary_agent", "packing_list_agent")
        self.graph.add_edge("packing_list_agent", "reminder_agent")

        # Set entry and exit nodes
        self.graph.set_entry_point("destination_parser")
        # self.graph.set_finish_point("flight_hotel_scraper") #tested, it works
        # self.graph.set_finish_point("itinerary_agent") #tested, it works
        # self.graph.set_finish_point("packing_list_agent") #testes, it works
        self.graph.set_finish_point("reminder_agent")
        # self.graph.set_exit_node("reminder_agent")

    def run(self, state: Union[str, Dict[str, Any], TravelBuddyState]):
        # 🔒 Coerce input safely (NO double-wrapping!)
        if isinstance(state, str):
            state = {"user_input": state}
        elif isinstance(state, TravelBuddyState):
            state = state.model_dump()  # already valid
        elif isinstance(state, dict):
            # Do NOT wrap; assume it's already flat
            if isinstance(state.get("user_input"), dict):
                # Defensive fix if something upstream nested it
                state["user_input"] = state["user_input"].get("user_input", "")
        else:
            raise TypeError(f"Unsupported input type: {type(state)}")

        # 🔍 Extra debug – leave this for now
        print("SUPERVISOR BEFORE INVOKE ->", state, type(state.get("user_input")))

        result = self.runnable_graph.invoke(state)
        return result
