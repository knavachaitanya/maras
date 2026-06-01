# backend/services/graphify_service.py
import json
import os

async def get_graph_data() -> dict:
    """Load the generated graphify graph data."""
    graph_path = os.path.join(os.path.dirname(__file__), "../../frontend/public/graph-data.json")
    
    if not os.path.exists(graph_path):
        return {"error": "Graph data not generated. Run: npm run graph"}
    
    with open(graph_path, "r", encoding="utf-8") as f:
        return json.load(f)
