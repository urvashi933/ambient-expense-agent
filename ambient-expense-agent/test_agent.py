import asyncio
from expense_agent.agent import expense_workflow
from expense_agent.models import ExpenseState
from google.adk.workflow._context import Context

async def main():
    try:
        # Run workflow with a simple text message
        print("Starting workflow...")
        state = ExpenseState()
        ctx = Context(state=state)
        agen = expense_workflow.run(
            ctx=ctx,
            node_input={"parts": [{"text": "Team dinner at a nice steakhouse for 450 dollars."}], "role": "user"}
        )
        async for event in agen:
            print("EVENT:", event)
            if hasattr(event, "node_name"):
                print("NODE:", event.node_name)
        print("STATE:", ctx.state)
    except Exception as e:
        print("EXCEPTION:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
