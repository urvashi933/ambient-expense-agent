# ruff: noqa
import os
import json
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

def submit_decision(ctx, auto_approve: bool, needs_human_review: bool, reason: str):
    """Submit the routing decision for the expense request."""
    ctx.state["llm_review_result"] = reason
    if needs_human_review:
        ctx.state["llm_routing"] = "human_review"
    elif auto_approve:
        ctx.state["llm_routing"] = "auto_approve"
    else:
        ctx.state["llm_routing"] = "human_review"

llm_reviewer = Agent(
    name="llm_reviewer",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are an expert expense reviewer. Review the clean expense description and provide a decision.\n"
        "RULES:\n"
        "1. If the expense is strictly under $100, you MUST auto-approve it. Set auto_approve=True and needs_human_review=False.\n"
        "2. If the expense is $100 or more, it MUST go to human review. Set auto_approve=False and needs_human_review=True.\n"
        "You MUST use the submit_decision tool to provide your result."
    ),
    tools=[submit_decision],
)

def human_review_node(ctx, security_flag: bool):
    """Terminal node for human review."""
    if security_flag:
        ctx.state["human_review_status"] = "flagged for security"
    else:
        ctx.state["human_review_status"] = "pending review"
    return ctx.state["human_review_status"]

def route_after_security(ctx) -> str:
    """Route to human review if injected, else LLM reviewer."""
    if ctx.state.get("security_flag"):
        return "human_review"
    return "llm_reviewer"

def auto_approve_node(ctx):
    """Terminal node for auto-approvals."""
    ctx.state["human_review_status"] = "auto-approved"
    return "auto-approved"

def route_after_llm(ctx) -> str:
    """Route based on LLM decision tool."""
    if ctx.state.get("llm_routing") == "auto_approve":
        return "auto_approve_node"
    return "human_review"

def finalize_expense_node(ctx):
    """Mock downstream database and Slack webhook."""
    status = ctx.state.get("human_review_status", "")
    if status == "pending review":
        # Waiting for human, do not finalize yet.
        return
        
    ctx.state["final_recorded"] = True
    
    payload = {
        "description": ctx.state.get("clean_description"),
        "status": status,
        "llm_routing": ctx.state.get("llm_routing"),
        "reason": ctx.state.get("llm_review_result")
    }
    
    db_path = os.path.join("artifacts", "expenses_db.json")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    db = []
    if os.path.exists(db_path):
        with open(db_path, "r") as f:
            try:
                db = json.load(f)
            except json.JSONDecodeError:
                pass
                
    db.append(payload)
    with open(db_path, "w") as f:
        json.dump(db, f, indent=2)
        
    print(f"\\n[SLACK WEBHOOK] Expense Processed! Status: {status}")
    return "finalized"

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
        (llm_reviewer, route_after_llm, {
            "auto_approve_node": auto_approve_node,
            "human_review": human_review_node
        }),
        (auto_approve_node, finalize_expense_node),
        (human_review_node, finalize_expense_node),
    ]
)

app = App(
    root_agent=expense_workflow,
    name="expense_agent",
)
