import requests
import time
import json

# Test the search endpoint
print("Testing /api/search endpoint...")
response = requests.post(
    "http://localhost:8000/api/search",
    json={"query": "phones under 80000"}
)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Response: {json.dumps(data, indent=2)}")

job_id = data.get("job_id")
if not job_id:
    print("ERROR: No job_id returned!")
    exit(1)

print(f"\nJob ID: {job_id}")
print("\nWaiting for results...")

# Poll for results
for i in range(30):
    time.sleep(2)
    response = requests.get(f"http://localhost:8000/api/results/{job_id}/logs")
    if response.status_code == 200:
        data = response.json()
        status = data.get("status")
        logs = data.get("logs", [])
        print(f"  [{i*2}s] Status: {status}, Logs: {len(logs)}")
        
        if status == "complete":
            output = data.get("output", "")
            print(f"\n{'='*60}")
            print("Pipeline Complete!")
            print(f"{'='*60}")
            print(f"Output length: {len(output)} characters")
            print(f"\nAll logs:")
            for log in logs:
                print(f"  [{log['agent']}] {log['event']}: {log['message'][:100]}")
            print(f"\nOutput preview:")
            print(output[:500] + "..." if len(output) > 500 else output)
            break
        elif status == "failed":
            print("\nERROR: Pipeline failed!")
            print("All logs:")
            for log in logs:
                print(f"  [{log['agent']}] {log['event']}: {log['message']}")
            break
    else:
        print(f"  Error fetching logs: {response.status_code}")

print("\nTest complete!")
