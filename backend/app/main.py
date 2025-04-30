import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.chat_router import router as chat_router
from app.routers.agent_router import router as agent_router
from app.routers.search_router import router as search_router

logging.basicConfig(level=logging.INFO)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routers
app.include_router(chat_router)
app.include_router(agent_router)
app.include_router(search_router)



@app.get("/")
async def root():
    return {"message": "LangGraph + LangChain backend running!"}
