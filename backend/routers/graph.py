from fastapi import APIRouter
from services.graphify_service import get_graph_data

router = APIRouter()

@router.get("/graph")
async def get_graph():
    return await get_graph_data()
