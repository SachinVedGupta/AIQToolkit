import json
import logging
import os
import httpx
from aiq.builder.builder import Builder
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from aiq.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)

class FlightSearchTool:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search.json"

    async def search_flights(self, client: httpx.AsyncClient, requirements: dict):
        params = {
            "engine": "google_flights",
            "api_key": self.api_key,
            "departure_id": requirements["departure"]["airport_code"],
            "arrival_id": requirements["arrival"]["airport_code"],
            "outbound_date": requirements["dates"]["departure"],
            "return_date": requirements["dates"]["return"],
            "currency": requirements["preferences"]["budget"]["currency"],
            "adults": requirements["travelers"]["adults"],
            "children": requirements["travelers"]["children"],
            "infants": requirements["travelers"]["infants"],
            "travel_class": requirements["preferences"]["class"][0],
            "max_stops": requirements["preferences"]["max_stops"]
        }

        try:
            r = await client.get(self.base_url, params=params)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as err:
            return {"error": f"HTTP error: {err.response.status_code}"}

def format_flight_results(results):
    if "error" in results:
        return f"Error searching flights: {results['error']}"
    
    formatted = ["### Top 3 Flight Options:\n"]
    
    # Get best flights or other flights
    flights = results.get("best_flights", []) or results.get("other_flights", [])
    
    for i, flight in enumerate(flights[:3], 1):
        formatted.append(f"#### Option {i}:")
        formatted.append(f"Price: ${flight['price']}")
        formatted.append(f"Total Duration: {flight['total_duration']} minutes")
        
        # Add flight details
        for f in flight["flights"]:
            formatted.append(f"\nFlight: {f['airline']} {f['flight_number']}")
            formatted.append(f"From: {f['departure_airport']['name']} ({f['departure_airport']['id']})")
            formatted.append(f"To: {f['arrival_airport']['name']} ({f['arrival_airport']['id']})")
            formatted.append(f"Time: {f['departure_airport']['time']} - {f['arrival_airport']['time']}")
            formatted.append(f"Duration: {f['duration']} minutes")
            formatted.append(f"Class: {f['travel_class']}")
            
            # Add amenities
            if "extensions" in f:
                formatted.append("Amenities:")
                for ext in f["extensions"]:
                    formatted.append(f"- {ext}")
        
        # Add layover information
        if "layovers" in flight:
            formatted.append("\nLayovers:")
            for layover in flight["layovers"]:
                formatted.append(f"- {layover['name']} ({layover['id']}): {layover['duration']} minutes")
        
        formatted.append("\n" + "="*50 + "\n")
    
    return "\n".join(formatted)

class FlightSearchConfig(FunctionBaseConfig, name="search_flights"):
    root_path: str
    api_key: str
    llm: LLMRef

@register_function(config_type=FlightSearchConfig)
async def search_flights_tool(config: FlightSearchConfig, builder: Builder):
    flight_search = FlightSearchTool(config.api_key)
    
    async def _arun(input_text: str) -> str:
        try:
            with open(config.root_path + "travel_requirements.json", 'r') as f:
                requirements = json.load(f)
        except FileNotFoundError:
            return "No travel requirements found. Please provide your travel preferences first."

        async with httpx.AsyncClient() as client:
            results = await flight_search.search_flights(client, requirements)
            
        return format_flight_results(results)

    return FunctionInfo.from_fn(
        _arun,
        description="Search for flights using stored travel requirements")