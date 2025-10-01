from pydantic import BaseModel, Field
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Policy Analysis Models
class PolicyAnalysis(BaseModel):
    Mitigation_Targets: List[str] = []
    Adaptation_Strategies: List[str] = []
    Finance_Commitments: List[str] = []
    Legislation_Policies: List[str] = []
    Stakeholders: List[str] = []
    Targets_Timelines: List[str] = []
    Sectors_Covered: List[str] = []
    Monitoring_Reporting: List[str] = []
    International_Cooperation: List[str] = []
    Institutional_Arrangements: List[str] = []
    Social_Community: List[str] = []
    Technology_Innovation: List[str] = []

# Weather Recommendation Models
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

# Policy Comparison Model
class ComparatorModel:
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    def compute_similarity(self, policy1: str, policy2: str) -> float:
        embedding = self.model.encode([policy1, policy2])
        similarity = cosine_similarity([embedding[0]], [embedding[1]])[0][0]
        return float(similarity)
    
    def extract_overlap_unique(self, policy1: str, policy2: str) -> dict:
        set1 = set(policy1.lower().split())
        set2 = set(policy2.lower().split())
        
        overlap = list(set1.intersection(set2))
        unique_policy1 = list(set1 - set2)
        unique_policy2 = list(set2 - set1)
        
        return {
            "overlap": overlap,
            "unique_policy1": unique_policy1,
            "unique_policy2": unique_policy2
        }