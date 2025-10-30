from dataclasses import dataclass, field
from typing import List, Dict, Any
import json
import folium

@dataclass
class Location:
    type: str
    coordinates: List[List[List[float]]]

@dataclass
class Field:
    crop: str
    activities: Dict[str, str]
    location: Location

@dataclass
class Crop:
    name: str


@dataclass
class Farm:
    name: str
    fields: List[Field] = field(default_factory=list)

def load_farm_from_json(filepath: str) -> Farm:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    farm_data = data["farm"]
    fields = [
        Field(
            crop=Crop(name=field["crop"]["name"]),
            activities=field["activities"],
            location=Location(
                type=field["location"]["type"],
                coordinates=field["location"]["coordinates"]
            )
        )
        for field in farm_data["fields"]
    ]
    return Farm(name=farm_data["name"], fields=fields)

def main():
    filepath = "../local_data/cluj_farm_1.json"
    farm = load_farm_from_json(filepath)
    
    # Print farm details to make sure they are loaded correctly
    print(f"Farm Name: {farm.name}")
    for field in farm.fields:
        print(f"  Crop: {field.crop}")
        print(f"  Activities: {field.activities}")
        print(f"  Location Type: {field.location.type}")
        print(f"  Coordinates: {field.location.coordinates}")

    # Center map on first field
    first_field = farm.fields[0]
    coords = first_field.location.coordinates[0]
    map_center = [coords[0][1], coords[0][0]]  # lat, lon

    farm_map = folium.Map(location=map_center, zoom_start=17)

    # Add each field to map
    for field in farm.fields:
        polygon = field.location.coordinates[0]
        # convert to [lat, lon]
        polygon_latlon = [[lat, lon] for lon, lat in polygon]

        folium.Polygon(
            locations=polygon_latlon,
            color="blue" if field.crop.name == "Sun Flower" else "green",
            fill=True,
            fill_opacity=0.4,
            #popup=f"{field['crop']} - Activities: {field['activities']}"
        ).add_to(farm_map)

    # Save to HTML
    farm_map.save("farm_map.html")
    print("✅ Map saved to farm_map.html – open this file in your browser")

if __name__ == "__main__":
    main()