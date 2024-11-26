import time
from sim import Sim
from led import LED
from loguru import logger
from server import Server
from tasker import Tasker
from multiprocessing.dummy import Process

server = Server()
sim = Sim()
tasker = Tasker()
led = LED()

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

