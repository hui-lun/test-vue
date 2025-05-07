import os
from dotenv import load_dotenv
from pymongo import MongoClient
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage # HumanMessage might not be used directly now but good to keep if agent expects it
from langchain_core.prompts import ChatPromptTemplate

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from pydantic import BaseModel
from typing import Any # For agent response type hinting

# Load environment variables from .env file
load_dotenv()

# --- FastAPI App Setup ---
app = FastAPI()

# --- Pydantic Model for Request Body ---
class QueryRequest(BaseModel):
    query: str

# --- Langchain Agent Setup (Copied from your original script) ---
# Initialize the language model
llm = ChatOpenAI(
    model="gemma-3-27b-it", # Make sure this model name is correct for your vLLM setup
    openai_api_key="EMPTY", # As per your original script
    openai_api_base=os.getenv("VLLM_API_BASE")
)

# 🔧 Define a tool: fetch weekly project update for a customer from MongoDB
@tool
def get_project_update(customer: str) -> str:
    """Find project weekly update for a specific customer name."""
    MONGODB_URI = f"mongodb://{os.getenv('MONGODB_USER')}:{os.getenv('MONGODB_PASSWORD')}@{os.getenv('MONGODB_IP')}:27017/admin"
    client = MongoClient(MONGODB_URI)
 
    db = client["BDM-mgmt"]         # ✅ Use the actual database name
    collection = db["BDM-mgmt"]     # ✅ Use the actual collection name
 
    # Handle field name with BOM prefix or special characters
    doc = collection.find_one({"\ufeffCustomer Name": customer})

    if not doc:
        return f"No project found for customer: {customer}"
    
    # Format selected fields into a summary string
    summary = f"🗂️ Project for {customer}:\n"
    summary += f"📌 Title: {doc.get('Title', 'N/A')}\n"
    summary += f"📅 Status: {doc.get('Status', 'N/A')}\n"
    summary += f"📦 Server Used: {doc.get('Server Used', 'N/A')}\n"
    summary += f"🧾 Volume: {doc.get('Volume', 'N/A')}\n\n"
    summary += f"📝 Weekly Updates:\n{doc.get('Weekly Update', 'No updates')}\n"
    return summary

# 🔧 Create a React-style agent and register the tool

# System message to guide the agent's tool usage
system_prompt = """IMPORTANT: Only use the 'get_project_update' tool if the user's question is specifically about 'weekly update'.
For all other types of questions (e.g., about BDM, company information, general knowledge, or anything not clearly a request for a project update report), you should try to answer directly using the database in MongoDB and your knowledge."""

prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=system_prompt),
        ("placeholder", "{messages}"), # Use a placeholder for messages
    ]
)

agent = create_react_agent(
    model=llm,
    tools=[get_project_update],
    prompt=prompt
)

# --- API Endpoints ---
@app.post("/chat")
async def chat_endpoint(request: QueryRequest) -> dict[str, Any]:
    """
    Receives a query, processes it with the Langchain agent, 
    and returns the agent's response.
    """
    try:
        # Format the message for the agent
        # The agent expects a list of messages.
        # For a simple query, we send a single user message.
        agent_input = {"messages": [HumanMessage(content=request.query)]}
        result = agent.invoke(agent_input)
        # The result structure from create_react_agent is typically {'messages': [AIMessage(...)]}
        # We might want to extract the content of the last AI message.
        # Adjust this based on the actual structure of 'result'
        if isinstance(result, dict) and "messages" in result and result["messages"]:
            # Get the last message, assuming it's the AI's response
            last_message = result["messages"][-1]
            if hasattr(last_message, 'content'):
                return {"response": last_message.content}
            else: # Fallback if content attribute is not found or message structure is different
                return {"response": str(last_message)} 
        return {"response": str(result)} # Fallback
    except Exception as e:
        print(f"Error in agent invocation: {e}") # Log error to server console
        return {"error": str(e)}

# --- Static Files Setup ---
# IMPORTANT: Replace 'frontend/dist' with the actual path to your frontend build output directory.
# This directory should contain your index.html and other static assets (JS, CSS, images).
FRONTEND_BUILD_DIR = "/home/ben/BDM-mgmt-test/frontend/dist" # EXAMPLE PATH! Please verify.

# Mount static files directory
# This makes files under FRONTEND_BUILD_DIR/assets accessible via /assets URL path
# If your assets are directly in FRONTEND_BUILD_DIR (e.g. main.js, style.css), 
# you might not need a separate "/static" mount or adjust path for index.html.
# For many SPAs, all assets are referenced from index.html relative to its location.
# Assuming your frontend build places assets like JS/CSS into an 'assets' subfolder.
# If not, you'll need to adjust this. For example, if main.js is at the root of FRONTEND_BUILD_DIR,
# and your index.html references <script src="/main.js">, you'd mount StaticFiles(directory=FRONTEND_BUILD_DIR) at "/"
# BUT that's tricky with API routes. A common pattern is:
# app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_BUILD_DIR, "static")), name="static_assets")
# or app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_BUILD_DIR, "assets")), name="assets")
# and ensure index.html uses relative paths like "assets/main.js" or "/assets/main.js"

# More robust approach for SPAs: serve index.html for the root and specific routes,
# and serve static assets from a specific path prefix.
# Check your frontend's build output structure and how index.html references assets.
# The following assumes assets are in an 'assets' subfolder within your FRONTEND_BUILD_DIR.
# e.g., FRONTEND_BUILD_DIR/assets/main.js
# and index.html references <script src="assets/main.js"></script> or <script src="/assets/main.js"></script>
# If your frontend router handles paths like /home, /profile, they should all serve index.html.

# Mount JS files
js_dir_path = os.path.join(FRONTEND_BUILD_DIR, "js")
if os.path.exists(js_dir_path):
    app.mount("/js", StaticFiles(directory=js_dir_path), name="js_assets")
else:
    print(f"Warning: Directory not found for JS assets: {js_dir_path}")

# Mount CSS files
css_dir_path = os.path.join(FRONTEND_BUILD_DIR, "css")
if os.path.exists(css_dir_path):
    app.mount("/css", StaticFiles(directory=css_dir_path), name="css_assets")
else:
    print(f"Warning: Directory not found for CSS assets: {css_dir_path}")

# You might need to add similar blocks for other specific asset types if they exist 
# in your 'dist' folder and are referenced by absolute paths in index.html, 
# e.g., /img, /fonts. Also, for specific files like /favicon.ico:
# favicon_path = os.path.join(FRONTEND_BUILD_DIR, "favicon.ico")
# if os.path.exists(favicon_path):
#    @app.get("/favicon.ico", include_in_schema=False)
#    async def favicon():
#        return FileResponse(favicon_path)

# This catch-all route for SPA should be AFTER specific static file mounts
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serves the main index.html file for SPA routing."""
    index_html_path = os.path.join(FRONTEND_BUILD_DIR, "index.html")
    if os.path.exists(index_html_path):
        return FileResponse(index_html_path)
    # If you want to distinguish API calls from frontend routes, you could check full_path here.
    # However, with /api prefix for backend, this generic catch-all for frontend is usually fine.
    return {"error": f"index.html not found at {index_html_path}. Ensure your frontend is built and FRONTEND_BUILD_DIR is set correctly."}


# --- Uvicorn Runner ---
if __name__ == "__main__":
    print(f"Starting server. Attempting to serve frontend from: {FRONTEND_BUILD_DIR}")
    print(f"Ensure your frontend is built and that directory contains index.html and its assets.")
    print(f"If assets are in a subfolder (e.g., 'assets' or 'static'), ensure app.mount is configured correctly above.")
    print(f"API will be available at http://localhost:8000/api/chat")
    print(f"Frontend should be served from http://localhost:8000/")
    
    # Check if FRONTEND_BUILD_DIR is valid before starting
    if not os.path.exists(FRONTEND_BUILD_DIR) or not os.path.isdir(FRONTEND_BUILD_DIR):
        print(f"Error: FRONTEND_BUILD_DIR '{FRONTEND_BUILD_DIR}' does not exist or is not a directory.")
        print("Please build your frontend and/or update the FRONTEND_BUILD_DIR variable in main.py.")
    elif not os.path.exists(os.path.join(FRONTEND_BUILD_DIR, "index.html")):
        print(f"Error: 'index.html' not found in '{FRONTEND_BUILD_DIR}'.")
        print("Please ensure your frontend is built correctly and index.html is present in the specified directory.")
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000)
