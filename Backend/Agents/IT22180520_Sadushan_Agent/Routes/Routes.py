from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from Backend.Agents.IT22180520_Sadushan_Agent.utils.Utils import sanitize_text, validate_policy_input
from Backend.Agents.IT22180520_Sadushan_Agent.Models.Comparator_model import compute_similarity, extract_overlap_unique
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from Backend.Agents.IT22180520_Sadushan_Agent.utils.Utils import sanitize_text, validate_policy_input
from Backend.Agents.IT22180520_Sadushan_Agent.Models.Comparator_model import compute_similarity, extract_overlap_unique

import os
import logging

#
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/policy_comparator.log",  
    level=logging.INFO,                      
    format="%(asctime)s - %(levelname)s - %(message)s"
)

router = APIRouter()

class ploicycomparter(BaseModel):
    policy1: str
    policy2: str

@router.post("/compare_policy")
def compare_policy(request: ploicycomparter):
    if not validate_policy_input(request.policy1) or not validate_policy_input(request.policy2):
        logging.warning("Invalid policy input detected")
        raise HTTPException(status_code=400, detail="Invalid or too short policy text")

    policy1 = sanitize_text(request.policy1)
    policy2 = sanitize_text(request.policy2)

    similarity_score = compute_similarity(policy1, policy2)
    comparation = extract_overlap_unique(policy1, policy2)

    
    logging.info(
        f"Policy comparison done | Similarity: {similarity_score:.2f} | "
        f"Overlap: {len(comparation['overlap'])} | "
        f"Unique A: {len(comparation['unique_policy1'])} | "
        f"Unique B: {len(comparation['unique_policy2'])}"
    )

    return {
        "similarity_score": similarity_score,
        "details": comparation
    }
