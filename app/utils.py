import os
import time
import uuid
import json
import socket
import psutil
import subprocess
from sim import Sim
import RPi.GPIO as GPIO
from loguru import logger
from datetime import timedelta
from pyttsreverso import pyttsreverso



class Utils():
    def __init__(self):
        self.convert = pyttsreverso.ReversoTTS()
        self.sim = Sim()
        self.relay_pin = 4
        self.bitrates = [22,96,128,192,320]
        self.supported_voices= [
        "Leila-Arabic",
        "Mehdi-Arabic",
        "Nizar-Arabic",
        "Salma-Arabic",
        "Lisa-Australian-English",
        "Tyler-Australian-English",
        "Jeroen-Belgian-Dutch",
        "Sofie-Belgian-Dutch",
        "Zoe-Belgian-Dutch",
        "Alice-BE-Belgian-French",
        "Anais-BE-Belgian-French",
        "Antoine-BE-Belgian-French",
        "Bruno-BE-Belgian-French",
        "Claire-BE-Belgian-French",
        "Julie-BE-Belgian-French",
        "Justine-Belgian-French",
        "Manon-BE-Belgian-French",
        "Margaux-BE-Belgian-French",
        "Marcia-Brazilian",
        "Graham-British",
        "Lucy-British",
        "Peter-British",
        "QueenElizabeth-British",
        "Rachel-British",
        "Louise-Canadian-French",
        "Laia-Catalan",
        "Eliska-Czech",
        "Mette-Danish",
        "Rasmus-Danish",
        "Daan-Dutch",
        "Femke-Dutch",
        "Jasmijn-Dutch",
        "Max-Dutch",
        "Samuel-Finland-Swedish",
        "Sanna-Finnish",
        "Alice-French",
        "Anais-French",
        "Antoine-French",
        "Bruno-French",
        "Claire-French",
        "Julie-French",
        "Manon-French",
        "Margaux-French",
        "Andreas-German",
        "Claudia-German",
        "Julia-German",
        "Klaus-German",
        "Sarah-German",
        "Kal-Gothenburg-Swedish",
        "Dimitris-Greek",
        "he-IL-Asaf-Hebrew",
        "Deepa-Indian-English",
        "Chiara-Italian",
        "Fabiana-Italian",
        "Vittorio-Italian",
        "Sakura-Japanese",
        "Minji-Korean",
        "Lulu-Mandarin-Chinese",
        "Bente-Norwegian",
        "Kari-Norwegian",
        "Olav-Norwegian",
        "Ania-Polish",
        "Monika-Polish",
        "Celia-Portuguese",
        "ro-RO-Andrei-Romanian",
        "Alyona-Russian",
        "Mia-Scanian",
        "Antonio-Spanish",
        "Ines-Spanish",
        "Maria-Spanish",
        "Elin-Swedish",
        "Emil-Swedish",
        "Emma-Swedish",
        "Erik-Swedish",
        "Ipek-Turkish",
        "Heather-US-English",
        "Karen-US-English",
        "Kenny-US-English",
        "Laura-US-English",
        "Micah-US-English",
        "Nelly-US-English",
        "Rod-US-English",
        "Ryan-US-English",
        "Saul-US-English",
        "Sharon-US-English",
        "Tracy-US-English",
        "Will-US-English",
        "Rodrigo-US-Spanish",
        "Rosa-US-Spanish",
    ]
        
    
    def tts(self,message,voice_name="Sharon-US-English",pitch=100,bitrate=128):
        try:
            file_name = f"{uuid.uuid4()}.mp3"
            data = self.convert.convert_text(voice=voice_name, pitch=pitch, bitrate=bitrate, msg=message)
            with open(file_name, "wb") as audio_file:
                    audio_file.write(data)
            logger.debug(file_name)
            return file_name
        except Exception as e:
            logger.error(f"Error creating audio file: {str(e)}")
            raise Exception(f"Error creating audio file: {str(e)}")

    def get_raspberry_pi_metrics(self):
        def format_size(value_bytes):
            """
            Converts a size in bytes to a human-readable format (GB, MB, or KB).
            """
            if value_bytes >= 1 << 30:  # Greater than or equal to 1 GB
                return f"{round(value_bytes / (1 << 30), 2)} GB"
            elif value_bytes >= 1 << 20:  # Greater than or equal to 1 MB
                return f"{round(value_bytes / (1 << 20), 2)} MB"
            else:  # Less than 1 MB, show in KB
                return f"{round(value_bytes / (1 << 10), 2)} KB"

        # Network status
        net_info = psutil.net_if_addrs()
        net_stats = psutil.net_if_stats()
        network_data = {}
        for iface, addrs in net_info.items():
            if iface in net_stats and net_stats[iface].isup:
                for addr in addrs:
                    if addr.family == socket.AF_INET:  # Use socket.AF_INET for IPv4
                        network_data[iface] = {
                            "connected": True,
                            "speed_mbps": net_stats[iface].speed,
                            "ip_address": addr.address,
                        }
        
        # CPU usage and temperature
        cpu_usage = psutil.cpu_percent(interval=1)
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                cpu_temp = round(int(f.read().strip()) / 1000.0, 2)  # Convert to Celsius, round to 2 decimals
        except FileNotFoundError:
            cpu_temp = None

        # Disk usage
        disk_usage = psutil.disk_usage("/")
        disk_data = {
            "total": format_size(disk_usage.total),
            "used": format_size(disk_usage.used),
            "free": format_size(disk_usage.free),
        }

        # RAM usage
        mem = psutil.virtual_memory()
        ram_data = {
            "total": format_size(mem.total),
            "used": format_size(mem.used),
            "free": format_size(mem.available),
        }

        # Core temperature
        try:
            core_temp = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
            core_temp = round(float(core_temp.split("=")[1].replace("'C", "").strip()), 2)
        except (FileNotFoundError, IndexError, ValueError):
            core_temp = None

        # Uptime
        try:
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.readline().split()[0])
                uptime_timedelta = timedelta(seconds=uptime_seconds)
                days = uptime_timedelta.days
                hours, remainder = divmod(uptime_timedelta.seconds, 3600)
                minutes = remainder // 60
                uptime = f"{days} days, {hours} hours, {minutes} minutes"
        except FileNotFoundError:
            uptime = None

        # Compile results
        data = {
            "network": network_data,
            "cpu": {
                "usage": round(cpu_usage, 2),
                "temp": cpu_temp,
            },
            "disk": disk_data,
            "ram": ram_data,
            "core_temp": core_temp,
            "uptime": uptime,
        }

        return data
    
    
    
    def get_supported_voices(self):
        return self.supported_voices
    
    