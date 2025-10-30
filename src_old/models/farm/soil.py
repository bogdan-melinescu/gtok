from dataclasses import dataclass
from typing import Optional

@dataclass
class Soil:
    type: str
    ph_approx: float
    fertility: str
    drainage: Optional[str] = None
    organic_carbon: Optional[str] = None