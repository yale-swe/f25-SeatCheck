

from fastapi import APIRouter
from app.auth import cas

router = APIRouter()
router.include_router(cas.router, prefix="", tags=["auth"])
