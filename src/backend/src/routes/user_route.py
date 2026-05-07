from fastapi import Request
from fastapi.responses import JSONResponse

from src.backend.db.chroma import collection
from src.backend.src.init import router
from backend.src.utils.scibert import nli_reranking

@router.get("/query")
async def get_queried_papers(request: Request):
    params = request.query_params

    query = params.get("query")
    start = int(params.get("start_year"))
    end = int(params.get("end_year"))

    results = collection.query(
        query_texts=[query],
        n_results=20,
        where={
            "year": {
                "$gte": start,
                "$lte": end
            }
        }
    )

    results = scibert_reranking(query, results)

    return JSONResponse(status_code=200, content=dict(results))