from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from octopus_brain.models import Resume

app = FastAPI()

@app.post("/analyze")
def analyze_resume(resume: Resume):
    return {"message": "Resume analyzed successfully"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        response = {"message": "Received: " + data}
        await websocket.send_json(response)