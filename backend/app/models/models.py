from pydantic import BaseModel

# /chat endpoint
class ChatRequest(BaseModel):
    query: str

# /agent-chat endpoint
class AgentChatRequest(BaseModel):
    email_content: str

# /search-and-summarize endpoint
class SearchAndSummarizeRequest(BaseModel):
    query: str