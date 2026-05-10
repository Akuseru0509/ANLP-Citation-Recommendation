from fastapi import FastAPI, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware

from .middlewares.query_middlewares import verify_query
from .routes.user_route import user_route


app = FastAPI()

router = APIRouter(
    prefix="/query",
    dependencies=[Depends(verify_query)]
)

app.include_router(router)


    
    