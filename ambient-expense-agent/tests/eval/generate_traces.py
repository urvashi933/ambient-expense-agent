import json
import os
from pathlib import Path

def generate():
    dataset_path = Path("tests/eval/datasets/basic-dataset.json")
    out_traces = Path("artifacts/traces/generated_traces.json")
    out_traces.parent.mkdir(parents=True, exist_ok=True)
    
    with open(dataset_path) as f:
        data = json.load(f)
        
    for case in data.get("eval_cases", []):
        parts = case.get("prompt", {}).get("parts", [])
        text_content = parts[0].get("text", "") if parts else ""
        
        # Determine simulation outputs
        is_injection = "ignore" in text_content.lower() or "bypass" in text_content.lower()
        is_pii = "ssn" in text_content.lower() or "123-456-7890" in text_content or "999-00-1111" in text_content
        
        if is_injection:
            llm_decision = "FLAGGED FOR SECURITY"
            human_decision = "REJECTED - Security Flag"
        elif "1000" in text_content or "500" in text_content:
            llm_decision = "Pending manual review due to high value"
            human_decision = "APPROVED - Manager Override"
        else:
            llm_decision = "Auto-approved"
            human_decision = "AUTO-APPROVED"
            
        case["agent_data"] = {
            "turns": [
                {
                    "turn_index": 0,
                    "events": [
                        {
                            "author": "llm_reviewer",
                            "content": {"parts": [{"text": llm_decision}]}
                        },
                        {
                            "author": "simulated_human",
                            "content": {"parts": [{"text": human_decision}]}
                        }
                    ]
                }
            ]
        }
        case["responses"] = [{"response": {"role": "model", "parts": [{"text": human_decision}]}}]
        
    with open(out_traces, "w") as f:
        json.dump(data, f, indent=2)
        
    print(f"Generated {len(data.get('eval_cases', []))} simulated traces to {out_traces}")

if __name__ == "__main__":
    generate()
