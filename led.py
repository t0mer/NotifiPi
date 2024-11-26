import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

class LED():
    def __init__(self):
        self.power_led = {'R': 17, 'G': 27, 'B': 22}  # Power Status LED
        self.service_led = {'R': 5, 'G': 6, 'B': 13}    # Service Status LED
        self.sim_status_led = {'R': 19, 'G': 26, 'B': 20}  # SIM Module Status LED
        self.operation_status_led = {'R': 21, 'G': 16, 'B': 12}  # Operation Status LED

        # Initialize GPIO


        # Set up the GPIO pins as outputs
        for led in [self.power_led, self.service_led, self.sim_status_led, self.operation_status_led]:
            for color, pin in led.items():
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)

    # Helper function to control LED colors
    def set_led_color(self, led, color):
        GPIO.output(led['R'], GPIO.HIGH if 'R' in color else GPIO.LOW)
        GPIO.output(led['G'], GPIO.HIGH if 'G' in color else GPIO.LOW)
        GPIO.output(led['B'], GPIO.HIGH if 'B' in color else GPIO.LOW)

    # Status control functions
    def power_on(self):
        self.set_led_color(self.power_led, 'G')  # Green for power ON

    def service_running(self):
        self.set_led_color(self.service_led, 'B')  # Blue for service running

    def service_not_running(self):
        self.set_led_color(self.service_led, 'R')  # Blue for service running

    def service_ready(self):
        self.set_led_color(self.service_led, 'G')  # Green for FastAPI ready

    def sim_not_ready(self):
        self.set_led_color(self.sim_status_led, 'R')  # Red for SIM not ready

    def sim_ready(self):
        self.set_led_color(self.sim_status_led, 'G')  # Green for SIM ready

    def sim_led_off(self):
        self.set_led_color(self.sim_status_led, '..')  # Turn SIM led off
        
    def operation_idle(self):
        self.set_led_color(self.operation_status_led, 'G')  # Green when idle

    def operation_active(self):
        self.set_led_color(self.operation_status_led, 'B')  # Blue when sending SMS or making a call


    def operation_off(self):
        self.set_led_color(self.operation_status_led, '..')  # Blue when sending SMS or making a call


    def test(self):
        # Simulate status changes
        try:
            self.power_on()
            time.sleep(2)

            self.service_running()
            time.sleep(2)

            self.service_ready()
            time.sleep(2)

            self.sim_not_ready()
            time.sleep(2)

            self.sim_ready()
            time.sleep(2)

            self.operation_idle()
            time.sleep(2)

            self.operation_active()
            time.sleep(2)

        finally:
            # Turn off all LEDs on exit
            for led in [self.power_led, self.service_led, self.sim_status_led, self.operation_status_led]:
                self.set_led_color(led, '')
            # GPIO.cleanup()


if __name__=="__main__":
    led = LED()
    led.test()