import uvicorn
import json
from fastapi import FastAPI
from controllers.PokeRequestController import (
    insert_pokemon_request, 
    update_pokemon_request, 
    select_pokemon_request, 
    get_all_request,
    delete_pokemon_request
)
from models.PokeRequest import PokeRequest
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return await insert_pokemon_request(pokemon_request)

@app.put("/request")
async def update_request(pokemon_request: PokeRequest):
    return await update_pokemon_request(pokemon_request)

@app.delete("/request/{id}")
async def delete_request(id: int):
    return await delete_pokemon_request(id)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)