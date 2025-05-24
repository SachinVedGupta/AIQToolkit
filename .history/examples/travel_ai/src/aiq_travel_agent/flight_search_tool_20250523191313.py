import json
import logging
import os
import httpx
from aiq.builder.builder import Builder
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from aiq.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)

def format_flight_results(results):
    if "error" in results:
        return f"Error searching flights: {results['error']}"
    
    flights = results.get("flights", [])[:3]  # Get top 3 flights
    if not flights:
        return "No flights found matching your criteria."
    
    formatted = "Top 3 flights found:\n\n"
    for i, flight in enumerate(flights, 1):
        formatted += f"{i}. {flight.get('airline', 'Unknown')} - "
        formatted += f"${flight.get('price', 'N/A')} - "
        formatted += f"{flight.get('departure_time', 'N/A')} to {flight.get('arrival_time', 'N/A')}\n"
    
    return formatted

class FlightSearchConfig(FunctionBaseConfig):
    _type: str = "aiq.tool/search_flights"
    root_path: str
    api_key: str
    llm: LLMRef

@register_function(config_type=FlightSearchConfig)
async def search_flights_tool(config: FlightSearchConfig, builder: Builder):
    async def _arun(input_text: str) -> str:
        try:
            with open(config.root_path + "travel_requirements.json", 'r') as f:
                requirements = json.load(f)
        except FileNotFoundError:
            return "No travel requirements found. Please provide your travel preferences first."

        params = {
            "engine": "google_flights",
            "api_key": config.api_key,
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

        async with httpx.AsyncClient() as client:
            r = await client.get("https://serpapi.com/search.json", params=params)
            r.raise_for_status()
            results = r.json()

        return format_flight_results(results)

    return FunctionInfo.from_fn(
        _arun,
        description="Search for flights using stored travel requirements")