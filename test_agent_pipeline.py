"""
Test script to verify the agent pipeline end-to-end.
This will test:
1. POST /api/search creates a session and starts the pipeline
2. Agents execute in order and log events
3. GET /api/results/{session_id}/logs returns agent logs
4. GET /api/results/{session_id} returns final results
"""

import asyncio
import httpx
import time
from datetime import datetime

API_URL = "http://localhost:8000"

async def test_agent_pipeline():
    print("=" * 80)
    print("AGENT PIPELINE END-TO-END TEST")
    print("=" * 80)
    print()
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: Submit a search query
        print("[1] Submitting search query...")
        query = "best laptops under 75000"
        
        try:
            response = await client.post(
                f"{API_URL}/api/search",
                json={"query": query, "fast_mode": False}  # Use real agent pipeline
            )
            response.raise_for_status()
            search_data = response.json()
            
            session_id = search_data.get("session_id")
            status = search_data.get("status")
            
            print(f"✅ Search submitted successfully")
            print(f"   Session ID: {session_id}")
            print(f"   Status: {status}")
            print()
            
        except Exception as e:
            print(f"❌ Search submission failed: {e}")
            return
        
        # Step 2: Poll for agent logs
        print("[2] Polling for agent logs...")
        print()
        
        agents_seen = set()
        max_polls = 30  # 30 seconds max
        
        for i in range(max_polls):
            try:
                # Get logs
                logs_response = await client.get(f"{API_URL}/api/results/{session_id}/logs")
                logs_response.raise_for_status()
                logs = logs_response.json()
                
                # Get results
                results_response = await client.get(f"{API_URL}/api/results/{session_id}")
                results_response.raise_for_status()
                results_data = results_response.json()
                
                current_status = results_data.get("status", "unknown")
                result_count = len(results_data.get("results", []))
                
                # Track which agents have logged
                for log in logs:
                    agent_name = log.get("agent_name")
                    event_type = log.get("event_type")
                    if agent_name and event_type == "complete":
                        agents_seen.add(agent_name)
                
                # Print status update
                print(f"   Poll {i+1}: Status={current_status}, Results={result_count}, "
                      f"Agents completed={sorted(agents_seen)}")
                
                # Check if complete
                if current_status in ["complete", "completed"]:
                    print()
                    print("✅ Pipeline completed!")
                    print()
                    break
                elif current_status == "error":
                    print()
                    print("❌ Pipeline failed with error status")
                    print()
                    break
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"   Poll {i+1}: Error - {e}")
                await asyncio.sleep(1)
        
        # Step 3: Verify agent logs
        print("[3] Verifying agent logs...")
        print()
        
        expected_agents = ["Orchestrator", "Research", "Analysis", "QA", "UIFormatter"]
        
        try:
            logs_response = await client.get(f"{API_URL}/api/results/{session_id}/logs")
            logs_response.raise_for_status()
            logs = logs_response.json()
            
            print(f"   Total logs: {len(logs)}")
            print()
            
            # Group logs by agent
            agent_logs = {}
            for log in logs:
                agent_name = log.get("agent_name")
                if agent_name not in agent_logs:
                    agent_logs[agent_name] = []
                agent_logs[agent_name].append(log)
            
            # Check each expected agent
            for agent in expected_agents:
                if agent in agent_logs:
                    events = [log.get("event_type") for log in agent_logs[agent]]
                    has_start = "start" in events
                    has_complete = "complete" in events
                    
                    status_icon = "✅" if (has_start and has_complete) else "⚠️"
                    print(f"   {status_icon} {agent}: {', '.join(events)}")
                else:
                    print(f"   ❌ {agent}: NO LOGS FOUND")
            
            print()
            
        except Exception as e:
            print(f"❌ Failed to verify logs: {e}")
            print()
        
        # Step 4: Verify final results
        print("[4] Verifying final results...")
        print()
        
        try:
            results_response = await client.get(f"{API_URL}/api/results/{session_id}")
            results_response.raise_for_status()
            results_data = results_response.json()
            
            status = results_data.get("status")
            results = results_data.get("results", [])
            
            print(f"   Status: {status}")
            print(f"   Result count: {len(results)}")
            print()
            
            if len(results) > 0:
                print("   Sample result:")
                sample = results[0]
                print(f"     Rank: {sample.get('rank')}")
                print(f"     Title: {sample.get('title', 'N/A')[:60]}...")
                print(f"     URL: {sample.get('url', 'N/A')[:60]}...")
                print(f"     Domain: {sample.get('domain', 'N/A')}")
                print(f"     Relevance: {sample.get('relevance_score', 0)}")
                print()
                print("✅ Results found and formatted correctly!")
            else:
                print("⚠️  No results returned")
            
            print()
            
        except Exception as e:
            print(f"❌ Failed to verify results: {e}")
            print()
        
        # Summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print()
        
        all_agents_completed = all(agent in agents_seen for agent in expected_agents)
        
        if all_agents_completed and len(results) > 0:
            print("✅ ALL TESTS PASSED")
            print("   - Search query submitted successfully")
            print("   - All 5 agents executed and logged events")
            print("   - Results were returned to the frontend")
        else:
            print("❌ SOME TESTS FAILED")
            if not all_agents_completed:
                missing = [a for a in expected_agents if a not in agents_seen]
                print(f"   - Missing agent logs: {missing}")
            if len(results) == 0:
                print("   - No results returned")
        
        print()

if __name__ == "__main__":
    print()
    print("Starting agent pipeline test...")
    print("Make sure the backend is running on http://localhost:8000")
    print()
    
    try:
        asyncio.run(test_agent_pipeline())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
