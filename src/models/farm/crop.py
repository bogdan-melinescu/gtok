from dataclasses import dataclass, field
from typing import List, Optional

from farm.fertilization import Fertilization

@dataclass
class Crop:
    type: str
    area_ha: float
    planting_date: str
    estimated_harvest_date: str
    seed_type: Optional[str] = None
    irrigation_needed: Optional[bool] = None
    fertilization: Optional[Fertilization] = None
    common_issues: List[str] = field(default_factory=list)
