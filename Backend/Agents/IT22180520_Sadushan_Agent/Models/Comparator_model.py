from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

model=SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def compute_similarity(policy1: str , policy2: str):
    embedding=model.encode([policy1,policy2])
    similarity = cosine_similarity([embedding[0]],[embedding[1]])[0][0]
    
    return float(similarity)

def extract_overlap_unique(policy1: str , policy2: str):
    set1=set(policy1.lower().split())
    set2=set(policy2.lower().split())
    
    overlap=list(set1.intersection(set2))
    unique_policy1 = list(set1 - set2)
    unique_policy2=list(set2 - set1)
    
    return {
        "overlap": overlap,
        "unique_policy1": unique_policy1,
        "unique_policy2": unique_policy2
    }