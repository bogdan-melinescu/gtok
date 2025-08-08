from dotenv import load_dotenv
import json
import os
import sys

from api.openweathermap import OpenWeatherAPI

def main():
    # Load environment variables from .env file
    load_dotenv(dotenv_path="/Users/bogdanmel/Development/gtok/.env")

    openweathermap_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    print("OpenWeatherAPI Key", openweathermap_api_key)

    # Create an instance of the OpenWeatherAPI class
    ow_api = OpenWeatherAPI(openweathermap_api_key)

    # Example: Get current weather
    weather = ow_api.get_weather(lat=45.76, lon=24.12)
    with open("/Users/bogdanmel/Development/gtok/local_data/weather.json", "w", encoding="utf-8") as file:
        json.dump(weather, file, indent=2)
    print(weather)

    # Example: Get forecast
    forecast = ow_api.get_forecast(lat=45.76, lon=24.12)
    with open("/Users/bogdanmel/Development/gtok/local_data/forecast.json", "w", encoding="utf-8") as file:
        json.dump(forecast, file, indent=2)
    print(forecast)

    # Example: Get air pollution data
    air_pollution = ow_api.get_air_pollution(lat=45.76, lon=24.12)
    with open("/Users/bogdanmel/Development/gtok/local_data/air_pollution.json", "w", encoding="utf-8") as file:
        json.dump(forecast, file, indent=2)
    print(air_pollution)

    # Example: Get tile URL
    #tile_url = ow_api.get_tile_url(layer="clouds_new", z=10, x=512, y=512)
    #print(tile_url)

if __name__ == "__main__":
    main()