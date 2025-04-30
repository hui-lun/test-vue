import logging

from fastapi import APIRouter
from app.models.models import AgentChatRequest
from app.agents.workflow import run_agent_workflow

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/agent-chat")
def agent_chat(req: AgentChatRequest):
    result = run_agent_workflow(req.email_content)
    # logger.debug("[DEBUG] /agent-chat triggered, email_content:", req.email_content)
    if hasattr(result, "dict"):
        result_dict = result.dict()
    else:
        result_dict = dict(result)
    return {"summary": result_dict.get("summary", ""), "full_result": result_dict}