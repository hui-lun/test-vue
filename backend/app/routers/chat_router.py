from fastapi import APIRouter
from app.models.models import ChatRequest
from app.agents.workflow import run_agent_workflow

router = APIRouter()

@router.post("/chat")
def chat(req: ChatRequest):
    # print("[DEBUG] /chat called, req.query:", req.query)
    result = run_agent_workflow(req.query)
    # print("[DEBUG] /chat run_agent_workflow result:", result)
    result_dict = dict(result)
    return {"summary": str(result_dict.get("summary", ""))}