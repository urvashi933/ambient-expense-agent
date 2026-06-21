import json
import urllib.request
import time

def start_run(prompt):
    req = urllib.request.Request(
        'http://localhost:8080/run',
        data=json.dumps({
            "appName": "expense_agent",
            "userId": "test-user",
            "stateDelta": {
                "prompt": prompt
            }
        }).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    resp = urllib.request.urlopen(req).read().decode()
    return json.loads(resp)

def get_session(session_id):
    resp = urllib.request.urlopen(f'http://localhost:8080/apps/expense_agent/users/test-user/sessions/{session_id}').read().decode()
    return json.loads(resp)

def resume_run(session_id, decision):
    req = urllib.request.Request(
        'http://localhost:8080/run',
        data=json.dumps({
            "appName": "expense_agent",
            "userId": "test-user",
            "sessionId": session_id,
            "stateDelta": {"human_review_status": decision}
        }).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    urllib.request.urlopen(req)

print("Starting run for $500 TV...")
events = start_run("Bought a new $500 TV for the office")
session_id = events[0]["invocationId"].split("-", 1)[1] if events else None

time.sleep(2)
state = get_session(session_id)["state"]
print("Status:", state.get("human_review_status"))

print("Resuming run with 'approved'...")
resume_run(session_id, "approved")

time.sleep(2)
state = get_session(session_id)["state"]
print("Final Recorded:", state.get("final_recorded"))
