import uuid
from loguru import logger
from pyttsreverso import pyttsreverso


class Utils():
    def __init__(self):
        self.convert = pyttsreverso.ReversoTTS()
    
    def tts(self,voice_name,message):
        try:
            file_name = f"{uuid.uuid4()}.mp3"
            data = self.convert.convert_text(voice=voice_name, pitch=100, bitrate=128, msg=message)
            with open(file_name, "wb") as audio_file:
                    audio_file.write(data)
            logger.debug(file_name)
            return file_name
        except Exception as e:
            logger.error(f"Error creating audio file: {str(e)}")
            raise Exception(f"Error creating audio file: {str(e)}")
        
        