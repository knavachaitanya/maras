from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.supabase_client import get_client
from services.result_store import result_store
import asyncio

router = APIRouter()

@router.websocket("/ws/agent-stream")
async def agent_stream(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Receive session_id from client
        data = await websocket.receive_json()
        session_id = data.get("session_id")
        
        if not session_id:
            await websocket.close(code=1008, reason="session_id required")
            return
        
        client = get_client()
        last_log_count = 0
        
        # Stream agent logs in real-time
        while True:
            memory_session = result_store.get_result(session_id)
            if memory_session:
                logs = memory_session.get("logs") or []
                if len(logs) > last_log_count:
                    for log in logs[last_log_count:]:
                        await websocket.send_json({
                            "type": "agent_status",
                            "agent": log.get("agent"),
                            "event": log.get("event"),
                            "status": event_to_status(log.get("event")),
                            "message": log.get("message"),
                            "timestamp": log.get("timestamp"),
                        })
                    last_log_count = len(logs)

                if memory_session.get("status") in ["complete", "failed", "error"]:
                    await websocket.send_json({"type": "complete", "status": memory_session.get("status")})
                    break
            elif client:
                logs = client.table("agent_logs").select("*").eq("session_id", session_id).order("created_at").execute()
                if len(logs.data) > last_log_count:
                    new_logs = logs.data[last_log_count:]
                    for log in new_logs:
                        await websocket.send_json({
                            "type": "agent_status",
                            "agent": log.get("agent_name"),
                            "event": log.get("event_type"),
                            "status": event_to_status(log.get("event_type")),
                            "message": log.get("message"),
                            "timestamp": log.get("created_at"),
                        })
                    last_log_count = len(logs.data)

                session = client.table("sessions").select("status").eq("id", session_id).execute()
                if session.data and session.data[0]["status"] in ["complete", "error"]:
                    await websocket.send_json({"type": "complete", "status": session.data[0]["status"]})
                    break
            
            await asyncio.sleep(0.5)
        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))


def event_to_status(event: str) -> str:
    if event == "start":
        return "active"
    if event == "complete":
        return "complete"
    if event == "error":
        return "error"
    return "active"
