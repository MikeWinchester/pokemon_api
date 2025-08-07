import uvicorn
import fastapi

app = fastapi.FastAPI()

@app.get("/version")
async def root():
    return {"version": "0.0.0`"}

if __name__== "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

