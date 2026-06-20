from pydantic import BaseModel, Field

class ExpenseInput(BaseModel):
    query: str = Field(..., description="The user's input related to expenses.")

class ExpenseOutput(BaseModel):
    response: str = Field(..., description="The agent's response to the user.")
