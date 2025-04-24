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
    allow_origins=["*"],  # 或指定網址 ["http://localhost", "https://yourdomain.com"]
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

@app.get("/")
def root():
    return {"message": "LangGraph + LangChain backend running!"}

from pydantic import BaseModel
from .agent import run_agent_workflow, fetch_and_analyze_web_html_node, ChatState
from .agent_search import search_and_summarize


class ChatRequest(BaseModel):
    query: str

class AgentChatRequest(BaseModel):
    email_content: str

class AnalyzeWebHtmlRequest(BaseModel):
    url: str

class SearchAndSummarizeRequest(BaseModel):
    query: str

@app.post("/agent-chat")
def agent_chat(req: AgentChatRequest):
    result = run_agent_workflow(req.email_content)
    # 只回傳 summary 給前端，或可依需求擴充
    return {"summary": result.get("summary", ""), "full_result": result}

@app.post("/chat")
def chat(req: ChatRequest):
    response = llm.invoke(req.query)
    # 強制轉為字串，避免 [object Object]
    if hasattr(response, "content"):
        text = response.content
    elif hasattr(response, "text"):
        text = response.text
    elif hasattr(response, "message"):
        text = response.message
    else:
        text = str(response)
    return {"response": text}

@app.post("/analyze-web-html")
def analyze_web_html(req: AnalyzeWebHtmlRequest):
    state = ChatState(email_content="", user_query=req.url, summary="")
    result = fetch_and_analyze_web_html_node(state)
    return {"summary": result["summary"], "full_result": result}

@app.post("/search-and-summarize")
def search_and_summarize_api(req: SearchAndSummarizeRequest):
    summary = search_and_summarize(req.query)
    return {"summary": summary}
