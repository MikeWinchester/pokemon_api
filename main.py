import uvicorn
import fastapi
import json
from utils.database import execute_query_json

app = fastapi.FastAPI()

@app.get("/")
async def root():
    query = "SELECT * FROM pokequeue.messages;"
    result = await execute_query_json(query)
    result_dict = json.loads(result)
    return result_dict

@app.get("/version")
async def version():
    return {"version": "0.1.0`"}

if __name__== "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

