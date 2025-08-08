from dataclasses import dataclass
from typing import List, Dict, Optional

from farm.crop import Crop
from farm.irrigation import Irrigation
from farm.soil import Soil

@dataclass
class Farm:
    farm_id: str
    farmer_name: str
    county: str
    location: Dict[str, float]
    total_area_ha: float
    crops: List[Crop]
    irrigation: Irrigation
    soil: Soil
    production_history: Dict[str, Dict[str, float]]
    market_prices: Dict[str, float]
    notes: Optional[str] = None