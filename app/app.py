import time
from sim import Sim
from led import LED
import RPi.GPIO as GPIO
from pathlib import Path
from loguru import logger
from server import Server
from tasker import Tasker
from multiprocessing.dummy import Process

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

server = Server()
sim = Sim()
tasker = Tasker()
led = LED()

audio_dir = Path.cwd() / "audio/"
audio_dir.mkdir(parents=True, exist_ok=True)

if __name__=="__main__":
    try:
        while not sim.is_sim_available():
            time.sleep(1)
            sim.power_on_sim()
        

        web_server = Process(target = server.run)
        web_server.start()

        task_manager = Process(target = tasker.run)
        task_manager.start()

        web_server.join()
        task_manager.join()
    except KeyboardInterrupt:
        logger.error("Exiting")
        led.service_not_running()
        led.sim_led_off()
        led.operation_off()

