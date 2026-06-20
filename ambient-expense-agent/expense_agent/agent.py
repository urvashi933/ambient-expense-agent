# ruff: noqa
import os
import google.auth

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.workflow import Workflow, START
from google.genai import types

from expense_agent.models import ExpenseState
from expense_agent.security import security_checkpoint

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id or "expense-agent-500015"
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# --- Nodes ---

llm_reviewer = Agent(
    name="llm_reviewer",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="You are an expert expense reviewer. Review the clean expense description and provide a decision.",
    tools=[],
)

def human_review_node(security_flag: bool) -> dict:
    """Terminal node for human review."""
    if security_flag:
        return {"human_review_status": "flagged for security"}
    return {"human_review_status": "pending review"}

def route_after_security(security_flag: bool) -> str:
    """Route to human review if injected, else LLM reviewer."""
    if security_flag:
        return "human_review"
    return "llm_reviewer"

# --- Workflow Graph ---

expense_workflow = Workflow(
    name="expense_workflow",
    state_schema=ExpenseState,
    edges=[
        (START, security_checkpoint),
        (security_checkpoint, route_after_security, {
            "human_review": human_review_node,
            "llm_reviewer": llm_reviewer
        }),
        (llm_reviewer, human_review_node),
    ]
)

app = App(
    root_agent=expense_workflow,
    name="expense_agent",
)
