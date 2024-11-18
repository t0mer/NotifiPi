import sim
import utils
import uvicorn
from loguru import logger
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException


app = FastAPI()
sim = sim.Sim()
utils = utils.Utils()



class SMSRequest(BaseModel):
    message: str
    phone_number: str
    
    
class TTSRequest(BaseModel):
    voice_name: str
    message: str
    phone_number: str


@app.post("/call/")
async def tts_endpoint(request: TTSRequest):
    try:
        audio_file_path = utils.tts(request.voice_name,request.message)
        sim.call_and_play(request.phone_number, audio_file_path)
        
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sms/")
async def text_endpoint(request: SMSRequest):
    sim.send_sms(request.phone_number,request.message)
    return {"message": "Received text"}



if __name__=="__main__":
   uvicorn.run(app, host="0.0.0.0", port=80) 