import time
import uvicorn
from sim import Sim
from led import LED
from tasker import Tasker
from utils import Utils
from loguru import logger
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException


class SMSRequest(BaseModel):
    message: str
    phone_number: str
    
    
class TTSRequest(BaseModel):
    voice_name: str
    message: str
    phone_number: str


class Server():
    def __init__(self):
        self.app = FastAPI()
        self.sim = Sim()
        self.utils = Utils()
        self.led = LED()
        self.tasker = Tasker()


        @self.app.on_event("startup")
        async def on_startup():
            self.led.service_ready()
            self.led.operation_idle()

        @self.app.on_event("shutdown")
        async def on_shutdown():
            self.led.service_not_running()
            self.led.sim_led_off()
            self.led.operation_off()




        @self.app.post("/call/")
        async def tts_endpoint(request: TTSRequest):
            try:
                audio_file_path = self.utils.tts(request.voice_name,request.message)
                self.sim.call_and_play(request.phone_number, audio_file_path)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/sms/")
        async def text_endpoint(request: SMSRequest):
            try:
                self.sim.send_sms(request.phone_number,request.message)
                return {"message": "Received text"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))


    def run(self):
        self.led.service_running()
        time.sleep(1)
        uvicorn.run(self.app, host="0.0.0.0", port=80) 

   