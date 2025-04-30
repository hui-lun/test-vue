import os
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.middleware.cors import CORSMiddleware

from app.routers.chat_router import router as chat_router
from app.routers.agent_router import router as agent_router
from app.routers.search_router import router as search_router


DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
def root():
    return {"message": "LangGraph + LangChain backend running!"}
