import time
import uvicorn
import asyncio
from sim import Sim
from led import LED
from tasker import Tasker
from utils import Utils
from loguru import logger
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.templating import Jinja2Templates
from concurrent.futures import ThreadPoolExecutor
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request


class SMSRequest(BaseModel):
    message: str
    phone_number: str
    
    
class TTSRequest(BaseModel):
    voice_name: str = "Sharon-US-English"
    message: str
    phone_number: str


class Server():
    def __init__(self):
        self.app = FastAPI(title="NotifiPi", description="Raspberry pi based notification service for text messages and calls", version='1.0.0', contact={"name": "Tomer Klein", "email": "tomer.klein@gmail.com", "url": "https://github.com/t0mer/wmd-servers-scrapper"})
        self.sim = Sim()
        self.utils = Utils()
        self.led = LED()
        self.tasker = Tasker()
        self.templates = Jinja2Templates(directory="templates/")
        self.origins = ["*"]
        self.executor = ThreadPoolExecutor()

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )



        @self.app.on_event("startup")
        async def on_startup():
            self.led.service_ready()
            self.led.operation_idle()

        @self.app.on_event("shutdown")
        async def on_shutdown():
            self.led.service_not_running()
            self.led.sim_led_off()
            self.led.operation_off()




        @self.app.post("/api/call/")
        async def tts_endpoint(request: TTSRequest):
            try:
                audio_file_path = self.utils.tts(request.message, request.voice_name)
                await asyncio.get_event_loop().run_in_executor(self.executor, self.sim.call_and_play, request.phone_number, audio_file_path)
                # self.sim.call_and_play(request.phone_number, audio_file_path)
                return {"message": ""}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/metrics/")
        async def metrics(request: Request):
            try:
                metrics = self.utils.get_raspberry_pi_metrics()
                return JSONResponse(content=jsonable_encoder(metrics))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/voices/")
        async def voices(request: Request):
            try:
                voices = self.utils.get_supported_voices()
                return JSONResponse(content=jsonable_encoder(voices))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))


        @self.app.post("/api/sms/")
        async def text_endpoint(request: SMSRequest):
            try:
                # self.sim.send_sms(request.phone_number,request.message)
                await asyncio.get_event_loop().run_in_executor(self.executor, self.sim.send_sms, request.phone_number, request.message)
                return {"message": ""}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/")
        async def home(request: Request):
            """
            Homepage
            """
            return self.templates.TemplateResponse('index.html', context={'request': request })


        @self.app.get("/status")
        async def home(request: Request):
            """
            Homepage
            """
            return self.templates.TemplateResponse('status.html', context={'request': request })

    def run(self):
        self.led.service_running()
        time.sleep(1)
        uvicorn.run(self.app, host="0.0.0.0", port=80) 

   