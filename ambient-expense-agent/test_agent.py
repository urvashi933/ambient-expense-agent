import asyncio
from expense_agent.agent import expense_workflow
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def main():
    try:
        print("Starting workflow...")
        session_service = InMemorySessionService()
        session = session_service.create_session_sync(user_id="test_user", app_name="test")
        runner = Runner(agent=expense_workflow, session_service=session_service, app_name="test")
        
        message = types.Content(
            role="user", parts=[types.Part.from_text(text="Team dinner at a nice steakhouse for 450 dollars.")]
        )

        for event in runner.run(
            new_message=message,
            user_id="test_user",
            session_id=session.id,
        ):
            print("EVENT:", event)
            if hasattr(event, "node_name"):
                print("NODE:", event.node_name)
    except Exception as e:
        print("EXCEPTION:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
