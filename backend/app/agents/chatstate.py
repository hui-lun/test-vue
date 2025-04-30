from typing_extensions import TypedDict

class ChatState(TypedDict):
    email_content: str
    user_query: str
    summary: str
    next_node: str