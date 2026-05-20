from fastapi import Request, APIRouter, Depends
from fastapi.responses import JSONResponse

from db.chroma import collection
from scripts.utils.scibert import ModelInference
from scripts.utils.llm import summarize
from scripts.middlewares.query_middlewares import verify_query

router = APIRouter(
    prefix="/query",
    dependencies=[Depends(verify_query)]
)

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
    start = params.get("start_year")
    end = params.get("end_year")

    results = collection.query(
        query_texts=[query],
        n_results=100,
        where={
            "$and": [
                {"year": {"$gte": int(start)}},
                {"year": {"$lte": int(end)}}
            ]
        }
    )

    reranker = request.app.state.reranker
    results = ModelInference.scibert_reranking(reranker, query, results, threshold=70.0)

    if results is None:
        return JSONResponse(
            status_code=404,
            content={
                "Error": "No Citation Found!"
            }
        )    

    results = summarize(results)

    print(results)

    return JSONResponse(
        status_code=200, 
        content=results
    )