import pytest
from expense_agent.agent import agent

@pytest.mark.asyncio
async def test_agent_name():
    """Verify that the agent initializes correctly."""
    assert agent.name == "expense_agent"
