import subprocess
payload = '{"amount": 150.0, "submitter": "alice@company.com", "category": "software", "description": "IDE License", "date": "2026-06-06"}'
subprocess.run(['uv', 'run', 'adk', 'run', 'expense_agent', payload])
