import time
import serial
import subprocess
from led import LED
import RPi.GPIO as GPIO
from loguru import logger
from pydantic import BaseModel



class Sim():
    def __init__(self):
        self.serial_port = "/dev/serial0"
        self.baud_rate = 9600
        self.timeout = 1
        self.serial = serial.Serial(self.serial_port,baudrate=self.baud_rate,timeout=self.timeout)
        self.led = LED()
        self.relay_pin = 4

        
        
    def send_at_command(self, command, delay=1):
        try:
            """ Helper function to send AT commands and read response """
            response = self.serial.write((command + '\r').encode())  # Ensure command is encoded to bytes
            time.sleep(delay)
            response = self.serial.read_all().decode()
            return response
        except Exception as e:
            logger.error(str(e))

    def is_sim_available(self):
        try:
            
            self.serial.write(b'AT\r')
            time.sleep(0.5)
            response = self.serial.read_all().decode().strip()
            if "OK" in response:
                logger.info("The SIM is ready")
                self.led.sim_ready()
                return True
            else:
                self.led.sim_not_ready()
                return False
        except Exception as e:
            logger.error(f"Error checking SIM module: {e}")
            return False

    def power_on_sim(self, delay=1):
        
        GPIO.setup(self.relay_pin, GPIO.OUT)  # Set the relay pin as an output  
        GPIO.output(self.relay_pin, GPIO.HIGH)  # Activate the relay (low-level trigger)
        time.sleep(2)                      # Hold for 1 second (adjust if needed)
        GPIO.output(self.relay_pin, GPIO.LOW)   # Deactivate the relay
        GPIO.setup(self.relay_pin, GPIO.IN)
        while not self.is_sim_available():
            time.sleep(delay)

    def ensure_sim_ready(self, delay=2, max_attempts=2):
        """
        Ensure the SIM module is ready.
        
        1. Check if the SIM is available.
        2. If not, power it on and wait for it to be available.
        3. If the SIM becomes available, return True; otherwise, return False.
        """
        attempts = 0
        while attempts < max_attempts:
            if self.is_sim_available():
                return True  # SIM is ready
            
            logger.warning(f"SIM not available. Attempting to power on (Attempt {attempts + 1}/{max_attempts})...")
            self.power_on_sim(delay=delay)
            
            # Wait briefly before re-checking
            time.sleep(delay)
            attempts += 1

        # If all attempts fail, log an error and return False
        logger.error("Failed to ensure SIM readiness after maximum attempts.")
        return False
        
    def utf8_to_ucs2(self, text):
        """ Convert UTF-8 string to UCS2 encoding for SMS """
        ucs2_encoded = ""
        for char in text:
            ucs2_encoded += f"{ord(char):04X}"
        return ucs2_encoded        

    def get_signal_quality(self):
        # Check signal quality
        response = self.send_at_command("AT+CSQ")
        logger.info(response)
        return response

    def set_sms_text_mode(self):
        # Set SMS mode to text mode
        response = self.send_at_command("AT+CMGF=1")
        logger.info(response)
        return response

    def set_ucs2_mode(self):
    # Set character set to UCS2 for sending non-ASCII messages
        response = self.send_at_command('AT+CSCS="UCS2"')
        logger.info(response)
        return response

    def set_sms_parameters(self):
    # Set SMS parameters (optional but recommended for UCS2)
        response = self.send_at_command("AT+CSMP=17,167,0,8")
        logger.info(response)
        return response
   
    def send_sms(self, phone_number, message, delay=2):
        try:
            
            # Prepare to send SMS
            self.ensure_sim_ready()
            self.led.operation_active()   
            self.set_sms_text_mode()
            self.set_ucs2_mode()
            self.set_sms_parameters()
            
            
            
            phone_number = self.utf8_to_ucs2(phone_number)
            message = self.utf8_to_ucs2(message)
            
            response = self.send_at_command(f'AT+CMGS="{phone_number}"')
            
            logger.info("Sending SMS Command Response:", response)

            # Check for the prompt character ">" before sending the message
            if ">" in response:
                # Send message and end with Ctrl+Z (ASCII 26)
                self.serial.write((message + chr(26)).encode('utf-8'))
                logger.info("Message sent to SIM808.")
            else:
                logger.error("Error: No prompt received, check SIM808 setup.")
                return False
            # Wait for the SMS send response
            time.sleep(2)
            final_response = self.serial.read_all().decode()
            logger.info("Final Response after sending SMS:", final_response)
            return True
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
        finally:
            self.led.operation_idle()

    def attempt_hangup(self):
        """ Attempts to hang up the call using multiple retries if needed """
        max_attempts = 5
        for attempt in range(max_attempts):
            logger.info(f"Attempting to hang up, try {attempt + 1} of {max_attempts}...")

            # Clear the serial buffer before sending the hangup command
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()

            # Try the ATH command first
            response = self.send_at_command("ATH", delay=1)
            
            # Check if the call is ended by looking for "NO CARRIER" or lack of "ERROR"
            if "NO CARRIER" in response or "OK" in response:
                logger.info("Call ended successfully.")
                return

            logger.error("ATH command failed or call not ended, retrying...")

        # If ATH didn't work, try AT+CHUP as a last resort
        logger.info("Attempting AT+CHUP as final hangup command.")
        response = self.send_at_command("AT+CHUP", delay=1)
        if "NO CARRIER" in response or "OK" in response:
            logger.info("Call ended with AT+CHUP.")
            return True
        else:
            logger.error("Failed to end the call with AT+CHUP as well. Manual intervention may be needed.")
            return False
        
    def call_and_play(self, phone_number, audio_file_path):
        """ Function to make a call, wait for answer, play an audio file, and hang up """
        try:
            self.ensure_sim_ready()
            self.led.operation_active()
            response = self.send_at_command(f'ATD{phone_number};')  # "ATD" command with ";" to initiate a voice call
            logger.info("Dialing number:", response)
            
            # Check if call was initiated successfully
            if "OK" in response:
                logger.info("Call initiated successfully, waiting for answer...")
            else:
                logger.error("Failed to initiate call")
                return False
            
            connected=False
            
            for _ in range(10):
                logger.info("Dailing...")
                logger.info(f"Serial in waiting: {self.serial.in_waiting}")
                logger.info(self.serial.read_all().decode())
                try:
                    if "1,0,0,0,0" in self.send_at_command("AT+CLCC",1):
                        logger.info("The call has been answered")
                        connected=True
                        break
                except:
                    pass
            
            connected=True    

            if not connected:
                logger.debug("No answer, hanging up.")
                self.attempt_hangup()
                return False

            # Wait 2 seconds before starting playback
            time.sleep(1)

            # Play the audio file using a system command (e.g., ffplay or mpg321)
            logger.info("Playing audio file...")
            subprocess.call(["ffplay", "-nodisp", "-autoexit", audio_file_path])

            # Wait 2 more seconds after playback
            time.sleep(2)
            
            # Hang up the call
            logger.info("Hanging up the call.")
            return self.attempt_hangup()
        except Exception as e:
            logger.error(e)
        finally:
            self.led.operation_idle()    
    