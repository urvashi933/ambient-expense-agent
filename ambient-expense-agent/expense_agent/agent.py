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

# Disable Vertex AI forcing so we can use the local GEMINI_API_KEY
# _, project_id = google.auth.default()
# os.environ["GOOGLE_CLOUD_PROJECT"] = project_id or "expense-agent-500015"
# os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
# os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# --- Nodes ---

from google.adk import Context

def submit_decision(tool_context: Context, auto_approve: bool = False, needs_human_review: bool = False, reason: str = ""):
    """Tool for LLM to record its routing decision."""
    tool_context.state["llm_review_result"] = reason
    if needs_human_review:
        tool_context.state["llm_routing"] = "human_review"
    elif auto_approve:
        tool_context.state["llm_routing"] = "auto_approve"
    else:
        tool_context.state["llm_routing"] = "human_review"

llm_reviewer = Agent(
    name="llm_reviewer",
    model=Gemini(
        model="gemini-flash-latest",
        # Note: If ADK wraps the GenAI SDK directly, ensure the kwarg maps properly to `http_options`
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

from google.adk.events import Event, RequestInput

def human_review_node_security(ctx, node_input=None):
    """Terminal node for human review flagged by security."""
    print("EXECUTING: human_review_node_security")
    if node_input and isinstance(node_input, dict) and "human_review_status" in node_input:
        ctx.state["human_review_status"] = node_input["human_review_status"]
        return node_input["human_review_status"]
    
    ctx.state["human_review_status"] = "pending review"
    # FIXED: Return the RequestInput instead of raising it
    return RequestInput("Waiting for human review")

def human_review_node_llm(ctx, node_input=None):
    """Terminal node for human review flagged by LLM."""
    print("EXECUTING: human_review_node_llm")
    if node_input and isinstance(node_input, dict) and "human_review_status" in node_input:
        ctx.state["human_review_status"] = node_input["human_review_status"]
        return node_input["human_review_status"]
        
    ctx.state["human_review_status"] = "pending review"
    # FIXED: Return the RequestInput instead of raising it
    return RequestInput("Waiting for human review")

def route_start(ctx, node_input=None) -> Event:
    """Route directly to finalization if human review is complete."""
    status = ctx.state.get("human_review_status")
    
    # Allow external trigger to provide the new status
    if node_input and isinstance(node_input, dict):
        if "human_review_status" in node_input:
            status = node_input["human_review_status"]
            ctx.state["human_review_status"] = status
            
    if status in ["approved", "rejected"]:
        return Event(route="finalize_expense_node")
    return Event(route="security_checkpoint")

def route_after_security(ctx) -> Event:
    """Route to human review if injected, else LLM reviewer."""
    print("EXECUTING: route_after_security")
    if ctx.state.get("security_flag"):
        print("ROUTING TO: human_review_node_security")
        return Event(route="human_review_node_security")
    print("ROUTING TO: llm_reviewer")
    return Event(route="llm_reviewer")

def auto_approve_node(ctx):
    """Terminal node for auto-approvals."""
    print("EXECUTING: auto_approve_node")
    ctx.state["human_review_status"] = "auto-approved"
    return "auto-approved"

def route_after_llm(ctx) -> Event:
    """Route based on LLM decision tool."""
    print("EXECUTING: route_after_llm")
    if ctx.state.get("llm_routing") == "auto_approve":
        print("ROUTING TO: auto_approve_node")
        return Event(route="auto_approve_node")
    print("ROUTING TO: human_review_node_llm")
    return Event(route="human_review_node_llm")

def finalize_expense_node(ctx):
    """Mock downstream database and Slack webhook."""
    status = ctx.state.get("human_review_status", "")
    print(f"\n[SLACK WEBHOOK] Expense Processed! Status: {status}")
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
        
    # FIXED: Replaced \\n with standard \n
    print(f"\n[SLACK WEBHOOK] Expense Processed! Status: {status}")
    return "finalized"

# --- Workflow Graph ---

expense_workflow = Workflow(
    name="expense_workflow",
    state_schema=ExpenseState,
    edges=[
        (START, route_start, {
            "finalize_expense_node": finalize_expense_node,
            "security_checkpoint": security_checkpoint
        }),
        (security_checkpoint, route_after_security, {
            "human_review_node_security": human_review_node_security,
            "llm_reviewer": llm_reviewer
        }),
        (llm_reviewer, route_after_llm, {
            "auto_approve_node": auto_approve_node,
            "human_review_node_llm": human_review_node_llm
        }),
        (auto_approve_node, finalize_expense_node),
        (human_review_node_security, finalize_expense_node),
        (human_review_node_llm, finalize_expense_node),
    ]
)

app = App(
    root_agent=expense_workflow,
    name="expense_agent",
)