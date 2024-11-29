import time
import schedule
from sim import Sim


class Tasker():
    def __init__(self):
        self.sim = Sim()
        
    
    def run(self):
        schedule.every(1).minutes.do(self.sim.ensure_sim_ready)
        while True:
            schedule.run_pending()
            time.sleep(1)