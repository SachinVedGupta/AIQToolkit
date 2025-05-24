

# AI Travel Agent

An intelligent travel assistant that helps users find and book flights using natural language. This agent leverages the AIQ toolkit plugin system and `Builder` to integrate with the Google Flights API through SerpAPI. The agent can understand natural language queries about flights, extract relevant information, and search for available options.

## Table of Contents

- [Key Features](#key-features)
- [Installation and Setup](#installation-and-setup)
  - [Install this Workflow](#install-this-workflow)
  - [Set Up API Keys](#set-up-api-keys)
- [Example Usage](#example-usage)
  - [Run the Workflow](#run-the-workflow)
- [Configuration](#configuration)
  - [Google Flights Function](#google-flights-function)
  - [ReAct Agent](#react-agent)

## Key Features

- **Natural Language Understanding:** Processes user queries in natural language to extract flight details
- **Google Flights Integration:** Searches for flights using the Google Flights API via SerpAPI
- **Travel Class Support:** Handles different travel classes (Economy, Premium Economy, Business, First)
- **ReAct Agent:** Uses reasoning and action to process user requests and make appropriate API calls
- **Configurable Workflow:** Fully configurable via YAML for flexibility and customization
- **Error Handling:** Robust error handling for API responses and invalid inputs

## Installation and Setup

If you have not already done so, follow the instructions in the [Install Guide](../../docs/source/quick-start/installing.md#install-from-source) to create the development environment and install AIQ toolkit.

### Install this Workflow

From the root directory of the AIQ toolkit library, run the following commands:

```bash
uv pip install -e examples/ai_travel_agent
```

### Set Up API Keys

The agent requires two API keys:

1. **SerpAPI Key** (for Google Flights):
   - Sign up at [SerpAPI](https://serpapi.com/)
   - Get your API key from the dashboard
   - Set it as an environment variable:
     ```bash
     export SERPAPI_API_KEY="your_serpapi_key"
     ```

2. **NVIDIA API Key** (for the LLM):
   - Sign up at [NVIDIA AI Endpoints](https://www.nvidia.com/en-us/ai-data-science/ai-endpoints/)
   - Get your API key from the dashboard
   - Set it as an environment variable:
     ```bash
     export NVIDIA_API_KEY="your_nvidia_key"
     ```

## Example Usage

### Run the Workflow

To search for flights, use the `aiq run` command:

```bash
aiq run --config_file=configs/config.yml --input "Find me a business class round-trip from JFK to LAX June 1-7"
```

The agent will:
1. Parse the natural language input
2. Extract flight details (airports, dates, travel class)
3. Search for available flights
4. Return the best flight options

## Configuration

### Google Flights Function

The `google_flights` function is configured in `configs/config.yml` with the following parameters:

```yaml
functions:
  google_flights:
    _type: google_flights
    currency: "USD"
    gl: "us"
    hl: "en"
    deep_search: false
    travel_class: 1  # 1=Economy, 2=Premium economy, 3=Business, 4=First
```

### ReAct Agent

The ReAct agent is configured to:
- Use NVIDIA's LLM for natural language understanding
- Process user queries and extract flight details
- Format the data for the Google Flights API
- Handle errors and retry failed requests

The agent's configuration in `configs/config.yml` includes:
- Tool configuration
- LLM settings
- Retry parameters
- Additional instructions for handling flight queries 