from fastapi import APIRouter
from .document_routes import document_router
from .policy_routes import policy_router

router = APIRouter()
router.include_router(document_router)
router.include_router(policy_router)
