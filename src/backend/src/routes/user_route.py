from fastapi import Request

from src.backend.db.chroma import collection
from src.backend.src.init import router

@router.get("/query")
async def get_queried_papers(request: Request):

