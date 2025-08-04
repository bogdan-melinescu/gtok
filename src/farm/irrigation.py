from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Irrigation:
    available: bool
    sources: List[str]
    future_plan: Optional[str] = None