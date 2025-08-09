import uvicorn
import json
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from controllers.PokeRequestController import (
    insert_pokemon_request, 
    update_pokemon_request, 
    select_pokemon_request, 
    get_all_request,
    delete_pokemon_request
)
from models.PokeRequest import PokeRequest
from fastapi.middleware.cors import CORSMiddleware
from utils.SSEManager import SSEManager

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancia global del SSE Manager
sse_manager = SSEManager()

@app.get("/")
async def root():
    return {"message": "Hello world!"}

@app.get("/version")
async def version():
    return {"version": "0.4.0"}

@app.get("/request/{id}")
async def select_request(id: int):
    return await select_pokemon_request(id)

@app.get("/request")
async def select_all_request():
    return await get_all_request()

@app.post("/request")
async def create_request(pokemon_request: PokeRequest):
    result = await insert_pokemon_request(pokemon_request)
    
    # Notificar a todos los clientes conectados
    await sse_manager.broadcast({
        "type": "report_created",
        "data": result
    })
    
    return result

@app.put("/request")
async def update_request(pokemon_request: PokeRequest):
    result = await update_pokemon_request(pokemon_request)
    
    # Notificar cambio de estado
    await sse_manager.broadcast({
        "type": "report_updated",
        "data": result
    })
    
    return result

@app.delete("/request/{id}")
async def delete_request(id: int):
    result = await delete_pokemon_request(id)
    
    # Notificar eliminación
    await sse_manager.broadcast({
        "type": "report_deleted",
        "data": {"id": id}
    })
    
    return result

@app.get("/events")
async def stream_events():
    """Endpoint para Server-Sent Events"""
    return StreamingResponse(
        sse_manager.stream(), 
        media_type="text/event-stream"  # ← CORRECTO
    )

# Endpoint para notificar progreso desde Azure Function
@app.post("/notify-progress")
async def notify_progress(notification: dict):
    """Endpoint para que Azure Function notifique el progreso"""
    await sse_manager.broadcast(notification)
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)