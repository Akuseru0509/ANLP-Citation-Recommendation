from contextlib import asynccontextmanager
from fastapi import FastAPI

from scripts.utils.scibert import ModelInference
from scripts.routes.user_route import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.reranker = ModelInference()
    print("Reranker Loaded!")
    yield
    app.state.reranker = None

app = FastAPI(lifespan=lifespan)

app.include_router(router)


    
    