from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.Utils import sanitize_text, validate_policy_input
from Backend.Agents.IT22180520_Sadushan_Agent.Models import compute_similarity, extract_overlap_and_unique


router=APIRouter()

class ploicycomparter(BaseModel):
    policy1:str
    policy2:str
    
@router.post("/compare_policy")

def  compare_policy (request: ploicycomparter):
        if not validate_policy_input(request.policy1) or not validate_policy_input(request.policy2):
            raise HTTPException(status_code=400,detail="Invalid or too short policy text")

        policy1=sanitize_text(request.policy1)
        policy2=sanitize_text(request.policy2)
        
        
        similarity_score=compute_similarity(policy1,policy2)
        
        comparation=extract_overlap_and_unique(policy1,policy2)
        
        return {
        "similarity_score": similarity_score,
        "details": comparation
    }