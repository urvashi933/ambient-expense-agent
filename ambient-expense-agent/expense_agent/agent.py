import os
from google.adk.agent import ReActAgent
from google.adk.model import GoogleModel
from google.adk.tools import tool

from expense_agent.config import PROJECT_ID, LOCATION
from expense_agent.models import ExpenseInput, ExpenseOutput

@tool
def record_expense(amount: float, category: str, description: str = "") -> str:
    """Record an expense with a given amount, category, and optional description."""
    return f"Successfully recorded expense: ${amount} for {category} ({description})"

# Initialize the Gemini model via ADK
model = GoogleModel(
    model_name="gemini-2.5-pro",
    project=PROJECT_ID,
    location=LOCATION,
)

# Create the ReAct agent
agent = ReActAgent[ExpenseInput, ExpenseOutput](
    name="expense_agent",
    description="An AI assistant that helps users track and manage their expenses.",
    model=model,
    tools=[record_expense],
    system_instruction="""You are a helpful expense management assistant.
Use your tools to record expenses when the user asks you to.
Always be polite and concise.""",
)
