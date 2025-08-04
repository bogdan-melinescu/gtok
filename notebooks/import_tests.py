import os
import sys
import json

project_root = "/Users/bogdanmel/Development/gtok"
os.chdir(project_root)

# Add the src directory to the Python path
sys.path.append(os.path.join(project_root, "src"))

from farm.farm import Farm, Crop, Irrigation, Soil

def main():
    # Set the working directory to the project root
    print("Working directory set to:", os.getcwd())
    print("Python path includes:", sys.path)

    with open("local_data/farm_cluj_no1.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    farm = Farm(**data)
    print(farm.farmer_name)

if __name__ == "__main__":
    main()