import logging

from fastapi import APIRouter
from app.models.models import SearchAndSummarizeRequest
from app.agents.search import search_and_summarize_advanced
from app.agents.test import search_and_fetch
from app.agents.workflow import run_agent_workflow

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/search-and-summarize")
def search_and_summarize_api(req: SearchAndSummarizeRequest):
    # result = run_agent_workflow(req.query)
    # if hasattr(result, "dict"):
    #     result_dict = result.dict()
    # else:
    #     result_dict = dict(result)
    # return {"summary": result_dict.get("summary", ""), "full_result": result_dict}

    summary = search_and_summarize_advanced(req.query)
    # summary = search_and_fetch(req.query)
    return {"summary": summary}