from .base_agent import BaseAgent
from src.schema.travel_models import TripRequest
from src.utils.logger import pretty_print
import os
import requests
import json

from dotenv import load_dotenv

load_dotenv()


class ItineraryAgent(BaseAgent):
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")

    def __call__(self, state):
        return self.run(state)

    def call_groq_llm(self, trip_request):
        # Unpacking trip request info
        destination = trip_request.get("destination", "the destination")
        start_date = trip_request.get("start_date", "")
        end_date = trip_request.get("end_date", "")
        preferences = trip_request.get("preferences", [])
        if isinstance(preferences, list):
            preferences_str = ", ".join(preferences)
        else:
            preferences_str = preferences or "general sightseeing"

        prompt = (
            f"Generate a detailed day-by-day travel itinerary for a trip to {destination} from {start_date} to {end_date}."
            f" The traveler prefers: {preferences_str}. "
            "Respond ONLY with a strict JSON array, where each element is a string describing the plan for one day. Do not include explanations, markdown, or any extra text."
            'Example: ["Day 1: ...", "Day 2: ..."]'
        )
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 350,
            "temperature": 0.7,
        }
        response = requests.post(url, headers=headers, json=payload)
        try:
            result = response.json()
        except Exception as e:
            print("Error decoding JSON from Groq:", e)
            print("Raw response:", response.text)
            raise RuntimeError(f"Groq did not return valid JSON: {response.text}")
        if "choices" not in result:
            print("Groq API error:", result)
            raise RuntimeError(f"Groq API returned error: {result}")
        return result["choices"][0]["message"]["content"]

    def run(self, input_data):
        trip_request = input_data.trip_request  # Access as attribute
        if not trip_request:
            return {"itinerary": [], "error": "No trip request provided"}
        llm_output = self.call_groq_llm(trip_request)
        # print("Raw LLM itinerary output:", llm_output)
        import re

        json_match = re.search(r"\[.*\]", llm_output, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            print("Could not find itinerary JSON in LLM output!")
            return {"itinerary": [], "error": "No itinerary JSON found in LLM output"}
        try:
            itinerary = json.loads(json_str)
            pretty_print("Itinerary:", itinerary)
            return {"itinerary": itinerary}
        except Exception as e:
            print("Error parsing itinerary JSON:", e)
            return {"itinerary": [], "error": str(e)}
