# src/agents/destination_parser.py
from dotenv import load_dotenv
from .base_agent import BaseAgent
from src.schema.travel_models import TripRequest
from src.utils.logger import pretty_print
import os
import requests
import json
import re

load_dotenv()


class DestinationParserAgent(BaseAgent):
    def __init__(self):
        # Load your Groq API key from environment
        self.groq_api_key = os.getenv("GROQ_API_KEY")

    def __call__(self, state):
        return self.run(state)

    def call_groq_llm(self, user_input):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }
        prompt = (
            "Extract the following fields from the user's travel request and output them as strict JSON (no explanations, no markdown, no comments): "
            "destination, start_date, end_date, budget, preferences. "
            "If a field is not mentioned, set it to null. "
            'User input: "' + user_input + '"'
            "\nJSON:"
        )
        payload = {
            "model": "llama3-8b-8192",  # Update if you use a different Groq-supported model
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300,
            "temperature": 0.0,
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
        # (implementation will go here)
        user_input = input_data.user_input
        llm_output = self.call_groq_llm(user_input)
        # print("Raw LLM output (destination_parser):", llm_output)
        json_match = re.search(r"\{.*\}", llm_output, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            print("Could not find JSON in LLM output!")
            return {"trip_request": None, "error": "No JSON found in LLM output"}
        try:
            trip_dict = json.loads(json_str)
            trip = TripRequest(**trip_dict)
            # --- Normalize preferences to list ---
            if isinstance(trip.preferences, str):
                trip.preferences = [trip.preferences]
            pretty_print("Trip Request:", trip.dict())
            return {"trip_request": trip.dict()}
        except Exception as e:
            print("Error parsing JSON:", e)
            return {"trip_request": None, "error": str(e)}
