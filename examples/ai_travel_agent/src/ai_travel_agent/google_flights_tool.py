# src/ai_travel_agent/google_flights_tool.py
import os
import aiohttp
import json
from aiq.cli.register_workflow import register_function
from aiq.data_models.function import FunctionBaseConfig
from aiq.builder.function_info import FunctionInfo
from aiq.builder.builder import Builder

class GoogleFlightsFunctionConfig(FunctionBaseConfig, name="google_flights"):
    """
    Call SerpAPI's Google Flights engine.
    """
    departure_id: str | None = None    # e.g. "JFK"
    arrival_id: str | None = None      # e.g. "LAX"
    outbound_date: str | None = None   # yyyy-mm-dd
    return_date: str | None = None     # yyyy-mm-dd
    currency: str = "USD"
    gl: str = "us"  # country
    hl: str = "en"  # language
    deep_search: bool = False
    travel_class: int = 1  # 1=Economy, 2=Premium economy, 3=Business, 4=First

@register_function(config_type=GoogleFlightsFunctionConfig)
async def google_flights_search(config: GoogleFlightsFunctionConfig, builder: Builder):
    """
    Queries SerpAPI's Google Flights engine and returns a summary
    of the very first "best_flights" itinerary.
    """
    async def _search_flights(input_data: str) -> str:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "❌ No SERPAPI_API_KEY in your environment."

        # Parse input data if provided, otherwise use config values
        try:
            if input_data:
                input_params = json.loads(input_data)
                # Handle both old and new parameter names
                params = {
                    "engine": "google_flights",
                    "departure_id": input_params.get("departure_id") or input_params.get("departureAirport") or config.departure_id,
                    "arrival_id": input_params.get("arrival_id") or input_params.get("arrivalAirport") or config.arrival_id,
                    "outbound_date": input_params.get("outbound_date") or input_params.get("departureDate") or config.outbound_date,
                    "return_date": input_params.get("return_date") or input_params.get("returnDate") or config.return_date,
                    "currency": config.currency,
                    "gl": config.gl,
                    "hl": config.hl,
                    "deep_search": str(config.deep_search).lower(),
                    "travel_class": input_params.get("travel_class", config.travel_class),
                    "api_key": api_key,
                }
            else:
                if not all([config.departure_id, config.arrival_id, config.outbound_date, config.return_date]):
                    return "❌ Missing required flight parameters. Please provide departure airport, arrival airport, departure date, and return date."
                
                params = {
                    "engine": "google_flights",
                    "departure_id": config.departure_id,
                    "arrival_id": config.arrival_id,
                    "outbound_date": config.outbound_date,
                    "return_date": config.return_date,
                    "currency": config.currency,
                    "gl": config.gl,
                    "hl": config.hl,
                    "deep_search": str(config.deep_search).lower(),
                    "travel_class": config.travel_class,
                    "api_key": api_key,
                }

            # Validate required parameters
            if not all([params["departure_id"], params["arrival_id"], params["outbound_date"], params["return_date"]]):
                return "❌ Missing required flight parameters. Please provide departure airport, arrival airport, departure date, and return date."

            async with aiohttp.ClientSession() as session:
                async with session.get("https://serpapi.com/search.json", params=params) as resp:
                    if resp.status != 200:
                        return f"Flight search failed ({resp.status}): {await resp.text()}"

                    data = await resp.json()
                    bf = data.get("best_flights")
                    if not bf:
                        return "No flights found."

                    leg = bf[0]["flights"][0]
                    dep = leg["departure_airport"]
                    arr = leg["arrival_airport"]
                    airline = leg.get("airline", "Unknown carrier")
                    duration = leg.get("duration", 0)
                    travel_class = {
                        1: "Economy",
                        2: "Premium Economy",
                        3: "Business",
                        4: "First"
                    }.get(params["travel_class"], "Economy")

                    return (
                        f"**{airline}** ({travel_class}) from {dep['id']} → {arr['id']}  \n"
                        f"{dep['time']} → {arr['time']}  \n"
                        f"Duration: {duration} min"
                    )
        except json.JSONDecodeError as e:
            return f"❌ Invalid JSON input: {str(e)}"
        except Exception as e:
            return f"❌ Error processing request: {str(e)}"

    yield FunctionInfo.from_fn(
        _search_flights,
        description="Search for flights using Google Flights API. Input should be a JSON string with 'departureAirport', 'arrivalAirport', 'departureDate', and 'returnDate' fields. Dates should be in YYYY-MM-DD format."
    )
