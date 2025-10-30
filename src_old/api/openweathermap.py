import requests

class OpenWeatherAPI:
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    TILE_URL = "https://tile.openweathermap.org/map"

    def __init__(self, api_key):
        self.api_key = api_key

    def get_weather(self, lat, lon):
        """Fetch current weather data."""
        url = f"{self.BASE_URL}/weather"
        params = {"lat": lat, "lon": lon, "appid": self.api_key}
        response = requests.get(url, params=params)
        return response.json()

    def get_forecast(self, lat, lon):
        """Fetch weather forecast data."""
        url = f"{self.BASE_URL}/forecast"
        params = {"lat": lat, "lon": lon, "appid": self.api_key}
        response = requests.get(url, params=params)
        return response.json()

    def get_air_pollution(self, lat, lon):
        """Fetch air pollution data."""
        url = f"{self.BASE_URL}/air_pollution"
        params = {"lat": lat, "lon": lon, "appid": self.api_key}
        response = requests.get(url, params=params)
        return response.json()

    #TODO: investigate later
    # def get_tile_url(self, layer, z, x, y):
    #     """Generate a tile URL for map layers."""
    #     return f"{self.TILE_URL}/{layer}/{z}/{x}/{y}.png?appid={self.api_key}"