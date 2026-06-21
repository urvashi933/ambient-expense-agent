from pydantic import BaseModel, Field

class ExpenseState(BaseModel):
    """The shared state for the expense workflow."""
    prompt: str = Field(default="", description="The raw, unedited expense description from the user.")
    clean_description: str = Field(default="", description="The description with PII scrubbed.")
    security_flag: bool = Field(default=False, description="True if a security event (e.g., prompt injection) was detected.")
    llm_review_result: str = Field(default="", description="The result from the LLM reviewer.")
    llm_routing: str = Field(default="", description="The routing decision from the LLM (auto_approve or human_review).")
    human_review_status: str = Field(default="pending", description="Status of human review: pending, flagged, auto-approved, approved, rejected.")
