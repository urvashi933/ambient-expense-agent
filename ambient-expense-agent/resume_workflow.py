import json
import urllib.request

req = urllib.request.Request(
    'http://localhost:8080/run',
    data=json.dumps({
        "appName": "expense_agent",
        "userId": "test-user",
        "sessionId": "e09cb2f3-df3c-46bb-a7c8-e7aa0f09fde6",
        "stateDelta": {"human_review_status": "approved"}
    }).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

print(urllib.request.urlopen(req).read().decode())
