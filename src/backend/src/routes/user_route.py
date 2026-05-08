from fastapi import Request
from fastapi.responses import JSONResponse

from src.backend.db.chroma import collection
from src.backend.src.init import router
from backend.src.utils.scibert import scibert_reranking

@router.post("/{paper_id}")
def add_ratings(paper_id: str):
    result = collection.get(ids=[paper_id], include=["metadatas"])

    if not result['ids']:
        return JSONResponse(
            status_code=404,
            content={
                "Error": "Paper not found!"
            }
        )

    metadata = result["metadatas"][0] if result["metadatas"] else {}

    current_likes = metadata.get("ratings", 0)
    new_likes = current_likes + 1

    metadata["ratings"] = new_likes

    collection.update(
        ids=[paper_id],
        metadatas=[metadata]
    )

    return JSONResponse(
        status_code=200,
        content={
            "Success": "Updated user ratings!"
        }
    )

@router.get("/")
def get_queried_papers(request: Request):
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