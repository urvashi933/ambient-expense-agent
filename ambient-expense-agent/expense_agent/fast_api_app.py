import base64
import logging
import subprocess
from fastapi import FastAPI, Request
from pydantic import BaseModel
import sys

# Configure standard Python logging for console logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("ambient_agent")

app = FastAPI()

class PubSubMessage(BaseModel):
    data: str
    messageId: str
    publishTime: str

class PubSubRequest(BaseModel):
    message: PubSubMessage
    subscription: str

@app.post("/")
async def pubsub_trigger(request: Request):
    """Event-driven entry point for Pub/Sub triggers."""
    try:
        body = await request.json()
        logger.info(f"Received Pub/Sub message body: {body}")
        
        # Extract message and subscription
        message = body.get("message", {})
        data_b64 = message.get("data", "")
        subscription = body.get("subscription", "")
        
        # Normalize the fully-qualified subscription path down to a short name
        # e.g. projects/expense-agent-500015/subscriptions/expense-trigger -> expense-trigger
        if "/" in subscription:
            short_name = subscription.split("/")[-1]
        else:
            short_name = subscription
            
        logger.info(f"Normalized subscription path: {short_name}")
        
        if not data_b64:
            logger.warning("No data found in Pub/Sub message.")
            return {"status": "success"} # Acknowledge empty messages
            
        # Decode base64 Pub/Sub payload
        decoded_bytes = base64.b64decode(data_b64)
        decoded_payload = decoded_bytes.decode('utf-8')
        logger.info(f"Decoded payload: {decoded_payload}")
        
        # Instantiate ADK workflow sessions using the subprocess runner to keep state
        # tracking native and avoid relying on experimental ADK internals
        cmd = ["uv", "run", "adk", "run", "expense_agent", decoded_payload]
        logger.info("Triggering ADK workflow session...")
        
        # Run synchronous subprocess. In a highly concurrent prod environment,
        # we would use asyncio.create_subprocess_exec.
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Workflow session completed successfully. Output: {result.stdout}")
        else:
            logger.error(f"Workflow session failed. Error: {result.stderr}")
            
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing Pub/Sub trigger: {e}")
        # Return 200 so Pub/Sub doesn't infinitely retry malformed messages
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
