from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class ComparisonRequest(BaseModel):
    policy1: str
    policy2: str

@router.post("/compare_policy")
async def compare_policies(request: ComparisonRequest):
    try:
        # Basic validation
        if not request.policy1 or not request.policy2:
            raise HTTPException(status_code=400, detail="Both policy texts are required")
        
        import spacy
        
        # Load English language model
        nlp = spacy.load("en_core_web_sm")
        
        # Process both texts
        doc1 = nlp(request.policy1)
        doc2 = nlp(request.policy2)
        
        # Calculate similarity
        similarity = doc1.similarity(doc2)
        
        # Extract key information
        policy1_entities = [{"text": ent.text, "label": ent.label_} for ent in doc1.ents]
        policy2_entities = [{"text": ent.text, "label": ent.label_} for ent in doc2.ents]
        
        # Find common entities
        common_entities = set(ent["text"] for ent in policy1_entities) & set(ent["text"] for ent in policy2_entities)
        
        return {
            "similarity_score": float(similarity),
            "common_entities": list(common_entities),
            "policy1_analysis": {
                "entities": policy1_entities,
                "word_count": len([token for token in doc1 if not token.is_punct])
            },
            "policy2_analysis": {
                "entities": policy2_entities,
                "word_count": len([token for token in doc2 if not token.is_punct])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))