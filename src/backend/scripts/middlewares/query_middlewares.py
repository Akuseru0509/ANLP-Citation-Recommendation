from fastapi import Request
from fastapi.responses import JSONResponse

def verify_query(request: Request):
    params = request.query_params

    if not params:
        return JSONResponse(
            status_code=400,
            content={
                "Error": "Missing Query Params"
            }
        )
    
    if (len(params.keys()) > 3):
        return JSONResponse(
            status_code=400,
            content={
                "Error": "Invalid Query Params"
            }
        )
    
    valid_keys = ["query", "start_year", "end_year"]

    for key in params.keys():
        if key not in valid_keys:
            return JSONResponse(
                status_code=400,
                content={
                    "Error": "Invalid Query Params"
                }
            )