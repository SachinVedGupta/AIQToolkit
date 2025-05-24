import json
import logging
import os
import re
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from aiq.builder.builder import Builder
from aiq.builder.framework_enum import LLMFrameworkEnum
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from aiq.data_models.component_ref import LLMRef
from aiq.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)

PROMPT_EXTRACT_TRAVEL_REQUIREMENTS = """
    You are a travel planning AI. Extract travel requirements from the user's input.
    Format your answer as valid JSON with the following structure:
    {
        "departure": {
            "airport_code": "string (3-letter IATA code)",
            "city": "string",
            "country": "string"
        },
        "arrival": {
            "airport_code": "string (3-letter IATA code)",
            "city": "string",
            "country": "string"
        },
        "dates": {
            "departure": "YYYY-MM-DD",
            "return": "YYYY-MM-DD",
            "flexible_dates": boolean
        },
        "preferences": {
            "budget": {
                "amount": number,
                "currency": "string"
            },
            "class": ["economy", "premium_economy", "business", "first"],
            "airlines": ["string"],
            "max_stops": number,
            "preferred_times": ["morning", "afternoon", "evening"]
        },
        "travelers": {
            "adults": number,
            "children": number,
            "infants": number
        }
    }

    Now process this travel request:
    \"\"\"{travel_request}\"\"\"
"""

def correct_json_format(response):
    try:
        json_start = response.find("{")
        if json_start == -1:
            raise ValueError("No JSON found in the response.")
        json_content = response[json_start:].strip()
        json_response = re.sub(r"```", "", json_content)
    except Exception as e:
        logger.exception("Error: %s", e, exc_info=True)
        json_response = response
    return json_response

class ExtractTravelRequirementsConfig(FunctionBaseConfig, name="extract_travel_requirements"):
    root_path: str
    llm: LLMRef

@register_function(config_type=ExtractTravelRequirementsConfig)
async def extract_travel_requirements(config: ExtractTravelRequirementsConfig, builder: Builder):
    llm = await builder.get_llm(llm_name=config.llm, wrapper_type=LLMFrameworkEnum.LANGCHAIN)
    prompt = PromptTemplate(
        input_variables=["travel_request"],
        template=PROMPT_EXTRACT_TRAVEL_REQUIREMENTS,
    )
    chain = LLMChain(llm=llm, prompt=prompt)

    async def _arun(input_text: str) -> str:
        response = await chain.arun(travel_request=input_text)
        response = correct_json_format(response)
        
        try:
            data = json.loads(response)
            filename = config.root_path + "travel_requirements.json"
            with open(filename, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file)
            return "Travel requirements extracted successfully. I can now search for flights."
        except json.JSONDecodeError as e:
            return "Error processing travel requirements. Please try again."

    return FunctionInfo.from_fn(
        _arun,
        description="Extract travel requirements from user input and store them for flight search")