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
    _type: str = "aiq.tool/serp_api"
    api_key: str
    llm: LLMRef

@register_function(config_type=FlightSearchConfig)
async def search_flights_tool(config: FlightSearchConfig, builder: Builder):
    async def _arun(input_text: str) -> str:
        try:
            with open("./examples/travel_ai/data/travel_requirements.json", 'r') as f:
                requirements = json.load(f)
        except FileNotFoundError:
            return "No travel requirements found. Please provide your travel preferences first."

        # Construct search query
        query = f"flights from {requirements['departure']['airport_code']} to {requirements['arrival']['airport_code']} on {requirements['dates']['departure']}"
        
        params = {
            "engine": "google_flights",
            "api_key": config.api_key,
            "q": query,
            "num": 3  # Get top 3 results
        }

        async with httpx.AsyncClient() as client:
            r = await client.get("https://serpapi.com/search.json", params=params)
            r.raise_for_status()
            results = r.json()

        return format_flight_results(results)

    return FunctionInfo.from_fn(
        _arun,
        description="Search for flights using stored travel requirements")