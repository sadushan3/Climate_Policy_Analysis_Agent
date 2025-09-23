from fastapi import APIRouter, HTTPException
from models.schemas import WeatherQuery, RecommendationResponse
from utils.recommender import recommend

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.post("/", response_model=RecommendationResponse)
def get_recommendations(q: WeatherQuery):
    try:
        result = recommend(q.dict(), top_n=5)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
