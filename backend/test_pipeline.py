import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.orchestrator import orchestrate_search
from services.result_store import result_store

async def test():
    query = "phones under 80000"
    job_id = "test-job-123"
    
    print(f"\n{'='*60}")
    print(f"Testing pipeline with query: {query}")
    print(f"{'='*60}\n")
    
    # Create the job first
    result_store.create_job(job_id, query)
    
    # Run the orchestrator
    await orchestrate_search(query, job_id)
    
    # Wait a bit for the result to be saved
    await asyncio.sleep(1)
    
    # Get the result
    result = result_store.get_result(job_id)
    
    if not result:
        print("ERROR: No result found!")
        return
    
    print(f"\n{'='*60}")
    print(f"Pipeline Status: {result['status']}")
    print(f"{'='*60}\n")
    
    # Print logs
    print("Logs:")
    for log in result.get('logs', []):
        print(f"  [{log['agent']}] {log['event']}: {log['message']}")
    
    # Print output
    print(f"\n{'='*60}")
    print("Output:")
    print(f"{'='*60}")
    output = result.get('output', '')
    if output:
        print(output[:500] + "..." if len(output) > 500 else output)
    else:
        print("NO OUTPUT GENERATED")
    
    print(f"\n{'='*60}")
    print(f"Output length: {len(output)} characters")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(test())
