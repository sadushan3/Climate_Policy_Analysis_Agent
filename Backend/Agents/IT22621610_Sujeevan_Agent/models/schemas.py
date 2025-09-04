from pydantic import BaseModel, Field
from typing import List, Optional

class WeatherQuery(BaseModel):
    location: str = Field(..., example="Colombo")
    month: int = Field(..., ge=1, le=12, example=8)
    temperature_c: float = Field(..., example=29.5)
    humidity_pct: int = Field(..., ge=0, le=100, example=78)
    wind_kmh: float = Field(..., ge=0, example=10.0)

class SimilarDay(BaseModel):
    location: str
    month: int
    temperature_c: float
    humidity_pct: int
    wind_kmh: float
    condition: str
    similarity: float

class RecommendationResponse(BaseModel):
    predicted_condition: str
    confidence: float
    top_similar_days: List[SimilarDay]
    message: Optional[str] = None
