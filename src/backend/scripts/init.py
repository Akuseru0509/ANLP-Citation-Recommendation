from fastapi import FastAPI, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware

from src.backend.scripts.middlewares.query_middlewares import verify_query
from src.backend.scripts.routes.user_route import user_route


app = FastAPI()

router = APIRouter(
    prefix="/query",
    dependencies=[Depends(verify_query)]
)

app.include_router(router)


    
    