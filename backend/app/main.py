from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from langchain_openai import ChatOpenAI
import os

DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LLM config
llm = ChatOpenAI(
    model="gemma-3-27b-it",
    openai_api_key="EMPTY",
    openai_api_base=os.getenv("VLLM_API_BASE")
)

from pydantic import BaseModel
from .agent import run_agent_workflow
from .agent_search import search_and_summarize_advanced


class ChatRequest(BaseModel):
    query: str

class AgentChatRequest(BaseModel):
    email_content: str

class SearchAndSummarizeRequest(BaseModel):
    query: str


@app.get("/")
def root():
    return {"message": "LangGraph + LangChain backend running!"}

@app.post("/agent-chat")
def agent_chat(req: AgentChatRequest):
    result = run_agent_workflow(req.email_content)
    print("[DEBUG] /agent-chat triggered, email_content:", req.email_content)
    if hasattr(result, "dict"):
        result_dict = result.dict()
    else:
        result_dict = dict(result)
    return {"summary": result_dict.get("summary", ""), "full_result": result_dict}

# @app.post("/chat")
# def chat(req: ChatRequest):
#     response = llm.invoke(req.query)
#     # 強制轉為字串，避免 [object Object]
#     if hasattr(response, "content"):
#         text = response.content
#     elif hasattr(response, "text"):
#         text = response.text
#     elif hasattr(response, "message"):
#         text = response.message
#     else:
#         text = str(response)
#     return {"response": text}
@app.post("/chat")
def chat(req: ChatRequest):
    print("[DEBUG] /chat called, req.query:", req.query)
    result = run_agent_workflow(req.query)
    print("[DEBUG] /chat run_agent_workflow result:", result)
    result_dict = dict(result)
    return {"summary": str(result_dict.get("summary", ""))}

@app.post("/search-and-summarize")
def search_and_summarize_api(req: SearchAndSummarizeRequest):
    # summary = search_and_summarize(req.query)
    summary = search_and_summarize_advanced(req.query)
    return {"summary": summary}
